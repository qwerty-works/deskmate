"""Read-only Google Calendar access and selection for the desk display."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import partial
import os
from pathlib import Path
import tempfile
import time

from google.auth.exceptions import GoogleAuthError, RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Http, HttpLib2Error
from oauthlib.oauth2 import OAuth2Error
from requests.exceptions import RequestException


SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]


def save_token(path, credentials):
    """Atomically replace the token, never creating a world-readable copy."""
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".token-", delete=False) as output:
            temporary = Path(output.name)
            os.fchmod(output.fileno(), 0o600)
            output.write(credentials.to_json())
        os.replace(temporary, path)
    except (OSError, ValueError) as exc:
        raise ValueError("Cannot save Google Calendar token; check the token path and permissions") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_credentials(credentials_path, token_path, authorize=False):
    """Only explicit authorization may open a browser; cron only refreshes."""
    token_path = Path(token_path)
    if authorize:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            credentials = flow.run_local_server(
                port=0, timeout_seconds=180, authorization_prompt_message="",
                success_message="Desk Mate Calendar authorized. You can close this tab.",
                access_type="offline", prompt="consent")
        except (OSError, ValueError, GoogleAuthError, OAuth2Error, RequestException) as exc:
            raise ValueError("Google Calendar authorization failed; check the Desktop OAuth client "
                             "JSON, consent settings, and network, then rerun --authorize on your Mac") from exc
    else:
        try:
            token_path.chmod(0o600)
            # Read the saved scopes, rather than assuming this token has our scope.
            credentials = Credentials.from_authorized_user_file(str(token_path))
        except (OSError, ValueError, TypeError) as exc:
            raise ValueError("Google Calendar token is missing or invalid; run --authorize on your Mac "
                             "and transfer the token to the Pi") from exc
    if not credentials.has_scopes(SCOPES) or not credentials.refresh_token:
        raise ValueError("Google Calendar token needs read-only event access and offline refresh; "
                         "rerun --authorize on your Mac")
    if not credentials.valid:
        try:
            credentials.refresh(partial(Request(), timeout=10))
        except RefreshError as exc:
            raise ValueError("Google Calendar authorization expired or was revoked; "
                             "rerun --authorize on your Mac and transfer the new token to the Pi") from exc
        except (GoogleAuthError, RequestException, OSError) as exc:
            raise ValueError("Google Calendar token refresh failed; check network access and retry") from exc
        if not credentials.valid:
            raise ValueError("Google Calendar token refresh did not succeed; rerun --authorize")
        save_token(token_path, credentials)
    elif authorize:
        save_token(token_path, credentials)
    return credentials


def calendar_service(credentials):
    """Use bundled discovery and bounded network requests on the Pi."""
    http = AuthorizedHttp(credentials, http=Http(timeout=10))
    return build("calendar", "v3", http=http, cache_discovery=False, static_discovery=True)


def fetch_events(service, now):
    """Fetch the complete window; errors never yield an empty or partial list."""
    now = now.astimezone(timezone.utc)
    query = {"calendarId": "primary", "timeMin": now.isoformat(),
             "timeMax": (now + timedelta(hours=24)).isoformat(),
             "singleEvents": True, "orderBy": "startTime", "showDeleted": False,
             "maxResults": 250}
    result = []
    seen_tokens = set()
    deadline = time.monotonic() + 45
    while True:
        try:
            page = service.events().list(**query).execute(num_retries=0)
        except RefreshError as exc:
            raise ValueError("Google Calendar authorization expired or was revoked; "
                             "rerun --authorize on your Mac and transfer the new token to the Pi") from exc
        except HttpError as exc:
            if exc.resp.status == 401:
                raise ValueError("Google Calendar HTTP 401; rerun --authorize on your Mac "
                                 "and transfer the new token to the Pi") from exc
            raise ValueError("Google Calendar HTTP %s; check API enablement, account access, "
                             "and quota, then retry" % exc.resp.status) from exc
        except (OSError, HttpLib2Error, GoogleAuthError, RequestException) as exc:
            raise ValueError("Google Calendar network request failed; check connectivity and retry") from exc
        except (ValueError, TypeError) as exc:
            raise ValueError("Google Calendar returned an invalid response; retry the fetch") from exc
        if time.monotonic() >= deadline:
            raise ValueError("Google Calendar fetch timed out; retry the fetch")
        if not isinstance(page, dict):
            raise ValueError("Google Calendar returned an invalid response; retry the fetch")
        # Google can omit an empty collection; an arbitrary empty object is
        # still an invalid response, not permission to remove the clock page.
        items = page.get("items", [] if page.get("kind") == "calendar#events" else None)
        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise ValueError("Google Calendar returned an invalid response; retry the fetch")
        result.extend(items)
        token = page.get("nextPageToken")
        if not token:
            return result
        if not isinstance(token, str) or token in seen_tokens:
            raise ValueError("Google Calendar returned an invalid response; retry the fetch")
        seen_tokens.add(token)
        query["pageToken"] = token


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: datetime
    end: datetime


def select_event(events, now):
    """Choose the earliest ongoing event, otherwise the next within 24 hours."""
    now = now.astimezone(timezone.utc)
    horizon = now + timedelta(hours=24)
    eligible = []
    for item in events:
        if item.get("status") == "cancelled":
            continue
        if any(attendee.get("self") is True and attendee.get("responseStatus") == "declined"
               for attendee in item.get("attendees", [])):
            continue
        if "date" in item.get("start", {}):
            continue
        try:
            start = datetime.fromisoformat(item["start"]["dateTime"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(item["end"]["dateTime"].replace("Z", "+00:00"))
            if start.utcoffset() is None or end.utcoffset() is None:
                raise ValueError("missing timezone")
            # UTC comparisons also handle the repeated hour at the end of DST.
            start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
            if end <= start:
                raise ValueError("invalid duration")
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise ValueError("Google Calendar returned an invalid timed event; retry the fetch") from exc
        if end > now and start < horizon:
            title = " ".join((item.get("summary") or "").split()) or "Untitled event"
            eligible.append(CalendarEvent(title, start, end))
    # Every ongoing event starts before every future event, so one sort suffices.
    return min(eligible, key=lambda value: value.start, default=None)


def event_payload(event, now, display_zone):
    """Render at push time and expire before the next start/end transition."""
    now = now.astimezone(timezone.utc)
    if event.end <= now:
        raise ValueError("Selected Calendar event ended during the fetch; rerun to refresh")
    if event.start <= now:
        text = "In progress " + event.title
        boundary = event.end
    else:
        local = event.start.astimezone(display_zone)
        today = now.astimezone(display_zone).date()
        if local.date() == today:
            prefix = ""
        elif local.date() == today + timedelta(days=1):
            prefix = "Tomorrow "
        else:
            # A 24-hour UTC window can reach two local dates ahead when DST starts.
            prefix = local.strftime("%b ") + str(local.day) + " "
        clock = local.strftime("%I:%M %p").lstrip("0")
        text = prefix + clock + " " + event.title
        boundary = event.start
    lifetime_ms = int(min(120, (boundary - now).total_seconds()) * 1000)
    if lifetime_ms < 1:
        raise ValueError("Selected Calendar event expires too soon; rerun to refresh")
    return {"text": text, "repeat": 1,
            "scroll": {"mode": "wrap", "speed": 100, "direction": "left",
                       "entry": "offscreen", "whenFits": "scroll"},
            "lifetimeMs": lifetime_ms, "lifetimeExpiry": "remove"}
