"""Calendar selection and display behavior, with a fixed UTC clock."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import redirect_stdout
import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from httplib2 import Response

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import google_calendar
from google_calendar import SCOPES, select_event, event_payload, fetch_events, load_credentials

NOW = datetime(2026, 10, 4, 16, 0, tzinfo=timezone.utc)
ZONE = ZoneInfo("America/New_York")


def event(start=NOW + timedelta(hours=1), end=NOW + timedelta(hours=2), **extra):
    return {"id": "meeting", "summary": "Team sync",
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()}, **extra}


class SelectionTests(unittest.TestCase):
    def test_earliest_future_event_regardless_of_input_order(self):
        later = event(start=NOW + timedelta(hours=3), end=NOW + timedelta(hours=4))
        selected = select_event([later, event()], NOW)
        self.assertEqual(selected.start, NOW + timedelta(hours=1))

    def test_ongoing_event_takes_priority_and_overlap_uses_earliest_start(self):
        earlier = event(start=NOW - timedelta(hours=2), summary="Earlier")
        later = event(start=NOW - timedelta(hours=1), summary="Later")
        self.assertEqual(select_event([event(), later, earlier], NOW).title, "Earlier")

    def test_excludes_all_day_cancelled_and_self_declined_events(self):
        excluded = [event(status="cancelled"),
                    event(attendees=[{"self": True, "responseStatus": "declined"}]),
                    {"start": {"date": "2026-10-04"}, "end": {"date": "2026-10-05"}}]
        self.assertIsNone(select_event(excluded, NOW))

    def test_other_attendee_decline_does_not_hide_event(self):
        self.assertIsNotNone(select_event([event(attendees=[{
            "self": False, "responseStatus": "declined"}])], NOW))

    def test_exact_start_is_in_progress_and_exact_end_is_excluded(self):
        selected = select_event([event(start=NOW)], NOW)
        self.assertEqual(event_payload(selected, NOW, ZONE)["text"], "In progress Team sync")
        self.assertIsNone(select_event([event(start=NOW - timedelta(hours=1), end=NOW)], NOW))

    def test_24_hour_upper_bound_is_exclusive(self):
        self.assertIsNone(select_event([event(start=NOW + timedelta(days=1),
                                            end=NOW + timedelta(days=1, hours=1))], NOW))

    def test_empty_calendar(self):
        self.assertIsNone(select_event([], NOW))

    def test_whitespace_and_missing_title(self):
        selected = select_event([event(summary="  Team\n\t sync  ")], NOW)
        self.assertEqual(selected.title, "Team sync")
        for title in (None, "", " \n "):
            with self.subTest(title=title):
                self.assertEqual(select_event([event(summary=title)], NOW).title, "Untitled event")

    def test_malformed_timed_event_fails_instead_of_looking_empty(self):
        for bad in ({"start": {"dateTime": "invalid"}},
                    event(start=NOW + timedelta(hours=2), end=NOW + timedelta(hours=1)),
                    {"start": {"dateTime": "2026-10-04T13:00:00"},
                     "end": {"dateTime": "2026-10-04T14:00:00"}}):
            with self.subTest(event=bad):
                with self.assertRaisesRegex(ValueError, "invalid timed event"):
                    select_event([bad], NOW)


class PayloadTests(unittest.TestCase):
    def test_upcoming_time_title_and_single_scroll(self):
        payload = event_payload(select_event([event()], NOW), NOW, ZONE)
        self.assertEqual(payload["text"], "1:00 PM Team sync")
        self.assertEqual(payload["repeat"], 1)
        self.assertEqual(payload["scroll"]["mode"], "wrap")
        self.assertEqual(payload["lifetimeMs"], 120000)
        self.assertEqual(payload["lifetimeExpiry"], "remove")

    def test_tomorrow_prefix_uses_display_timezone(self):
        selected = select_event([event(start=NOW + timedelta(hours=21),
                                       end=NOW + timedelta(hours=22))], NOW)
        self.assertEqual(event_payload(selected, NOW, ZONE)["text"],
                         "Tomorrow 9:00 AM Team sync")

    def test_expiration_is_capped_at_start_or_end(self):
        for start, end in ((NOW + timedelta(seconds=30), NOW + timedelta(minutes=5)),
                           (NOW - timedelta(minutes=5), NOW + timedelta(seconds=30))):
            with self.subTest(start=start):
                payload = event_payload(select_event([event(start=start, end=end)], NOW), NOW, ZONE)
                self.assertEqual(payload["lifetimeMs"], 30000)

    def test_event_that_ended_during_preflight_is_not_pushed(self):
        selected = select_event([event()], NOW)
        with self.assertRaisesRegex(ValueError, "ended"):
            event_payload(selected, NOW + timedelta(hours=2), ZONE)

    def test_start_crossed_during_preflight_changes_to_in_progress(self):
        selected = select_event([event(start=NOW + timedelta(seconds=1))], NOW)
        payload = event_payload(selected, NOW + timedelta(seconds=2), ZONE)
        self.assertEqual(payload["text"], "In progress Team sync")

    def test_dst_fallback_uses_absolute_instants(self):
        now = datetime(2026, 11, 1, 5, 45, tzinfo=timezone.utc)
        selected = select_event([event(start=datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc),
                                       end=datetime(2026, 11, 1, 7, 30, tzinfo=timezone.utc))], now)
        self.assertEqual(event_payload(selected, now, ZONE)["text"], "1:30 AM Team sync")

    def test_dst_spring_forward(self):
        now = datetime(2026, 3, 8, 6, 45, tzinfo=timezone.utc)
        selected = select_event([event(start=datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc),
                                       end=datetime(2026, 3, 8, 8, 30, tzinfo=timezone.utc))], now)
        self.assertEqual(event_payload(selected, now, ZONE)["text"], "3:30 AM Team sync")

    def test_24_hours_across_spring_dst_can_reach_day_after_tomorrow(self):
        now = datetime(2026, 3, 8, 4, 45, tzinfo=timezone.utc)  # Mar 7, 11:45 PM locally
        start = now + timedelta(hours=23, minutes=45)  # Mar 9, 12:30 AM locally
        selected = select_event([event(start=start, end=start + timedelta(hours=1))], now)
        self.assertEqual(event_payload(selected, now, ZONE)["text"], "Mar 9 12:30 AM Team sync")


class FetchTests(unittest.TestCase):
    def test_valid_google_empty_response_may_omit_items(self):
        service = Mock()
        service.events.return_value.list.return_value.execute.return_value = {"kind": "calendar#events"}
        self.assertEqual(fetch_events(service, NOW), [])

    def test_real_google_client_builds_authenticated_paginated_requests(self):
        # Exercise discovery, URL encoding, authorization and JSON decoding;
        # replace only the external HTTP transport.
        http = Mock()
        http.request.side_effect = [
            (Response({"status": "200"}), json.dumps({"items": [event()], "nextPageToken": "two"}).encode()),
            (Response({"status": "200"}), json.dumps({"items": []}).encode())]
        with patch("google_calendar.Http", return_value=http):
            service = google_calendar.calendar_service(credentials())
            try:
                self.assertEqual(fetch_events(service, NOW), [event()])
            finally:
                service.close()
        first, second = http.request.call_args_list
        self.assertIn("/calendar/v3/calendars/primary/events?", first.args[0])
        self.assertIn("singleEvents=true", first.args[0])
        self.assertIn("orderBy=startTime", first.args[0])
        self.assertEqual(first.kwargs["headers"]["authorization"], "Bearer private-access-token")
        self.assertIn("pageToken=two", second.args[0])

    def test_recurring_instances_and_pagination(self):
        service = Mock()
        recurring = event(recurringEventId="series")
        service.events.return_value.list.return_value.execute.side_effect = [
            {"items": [event()], "nextPageToken": "second"}, {"items": [recurring]}]
        result = fetch_events(service, NOW)
        self.assertEqual(result, [event(), recurring])
        calls = service.events.return_value.list.call_args_list
        self.assertEqual(calls[0].kwargs, {
            "calendarId": "primary", "timeMin": NOW.isoformat(),
            "timeMax": (NOW + timedelta(hours=24)).isoformat(),
            "singleEvents": True, "orderBy": "startTime", "showDeleted": False,
            "maxResults": 250})
        self.assertEqual(calls[1].kwargs["pageToken"], "second")

    def test_failed_second_page_does_not_return_partial_result_or_log_secrets(self):
        service = Mock()
        error = HttpError(Response({"status": "403"}), b'{"error":{"message":"secret title"}}')
        service.events.return_value.list.return_value.execute.side_effect = [
            {"items": [event()], "nextPageToken": "second"}, error]
        with self.assertRaisesRegex(ValueError, "HTTP 403") as caught:
            fetch_events(service, NOW)
        self.assertNotIn("secret title", str(caught.exception))

    def test_network_failure_is_actionable(self):
        service = Mock()
        service.events.return_value.list.return_value.execute.side_effect = OSError("secret")
        with self.assertRaisesRegex(ValueError, "network") as caught:
            fetch_events(service, NOW)
        self.assertNotIn("secret", str(caught.exception))

    def test_revocation_during_api_request_requires_reauthorization(self):
        service = Mock()
        service.events.return_value.list.return_value.execute.side_effect = RefreshError("private-token")
        with self.assertRaisesRegex(ValueError, "--authorize") as caught:
            fetch_events(service, NOW)
        self.assertNotIn("private-token", str(caught.exception))

    def test_fetch_deadline_does_not_return_partial_results(self):
        service = Mock()
        service.events.return_value.list.return_value.execute.return_value = {"items": [event()]}
        with patch("google_calendar.time.monotonic", side_effect=[0, 46]):
            with self.assertRaisesRegex(ValueError, "timed out"):
                fetch_events(service, NOW)

    def test_malformed_response_never_looks_empty(self):
        for response in (None, {}, {"items": "bad"}, {"items": [None]}):
            with self.subTest(response=response):
                service = Mock()
                service.events.return_value.list.return_value.execute.return_value = response
                with self.assertRaisesRegex(ValueError, "invalid response"):
                    fetch_events(service, NOW)

    def test_repeated_pagination_token_fails(self):
        service = Mock()
        service.events.return_value.list.return_value.execute.return_value = {
            "items": [], "nextPageToken": "same"}
        with self.assertRaisesRegex(ValueError, "invalid response"):
            fetch_events(service, NOW)


def credentials(expired=False, scopes=SCOPES, refresh_token="private-refresh-token"):
    return Credentials("private-access-token", refresh_token=refresh_token,
                       token_uri="https://oauth2.googleapis.com/token",
                       client_id="client", client_secret="private-client-secret", scopes=scopes,
                       expiry=datetime(2000 if expired else 2099, 1, 1))


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.token = self.root / "private" / "token.json"
        self.client = self.root / "credentials.json"

    def write_token(self, value):
        self.token.parent.mkdir(exist_ok=True)
        self.token.write_text(value.to_json())

    def test_missing_token_never_opens_browser(self):
        with patch("google_calendar.InstalledAppFlow") as flow:
            with self.assertRaisesRegex(ValueError, "--authorize"):
                load_credentials(self.client, self.token)
            flow.assert_not_called()

    def test_valid_token_is_restricted_to_owner_and_does_not_refresh(self):
        self.write_token(credentials())
        self.token.chmod(0o644)
        with patch.object(Credentials, "refresh") as refresh:
            self.assertTrue(load_credentials(self.client, self.token).valid)
            refresh.assert_not_called()
        self.assertEqual(self.token.stat().st_mode & 0o777, 0o600)

    def test_expired_token_is_refreshed_and_saved(self):
        self.write_token(credentials(expired=True))

        def refreshed(value, request):
            value.token = "replacement-access-token"
            value.expiry = datetime(2099, 1, 1)

        with patch.object(Credentials, "refresh", autospec=True, side_effect=refreshed):
            value = load_credentials(self.client, self.token)
        self.assertTrue(value.valid)
        self.assertEqual(json.loads(self.token.read_text())["token"], "replacement-access-token")
        self.assertEqual(self.token.stat().st_mode & 0o777, 0o600)

    def test_revoked_token_never_opens_browser_or_exposes_provider_error(self):
        self.write_token(credentials(expired=True))
        with patch.object(Credentials, "refresh", side_effect=RefreshError("private-refresh-token")), \
                patch("google_calendar.InstalledAppFlow") as flow:
            with self.assertRaisesRegex(ValueError, "--authorize") as caught:
                load_credentials(self.client, self.token)
            self.assertNotIn("private-refresh-token", str(caught.exception))
            flow.assert_not_called()

    def test_wrong_scope_and_missing_refresh_token_require_authorization(self):
        for value in (credentials(scopes=["openid"]), credentials(refresh_token=None)):
            with self.subTest(scopes=value.scopes):
                self.write_token(value)
                with self.assertRaisesRegex(ValueError, "--authorize"):
                    load_credentials(self.client, self.token)

    def test_corrupt_token_requires_authorization(self):
        self.token.parent.mkdir()
        self.token.write_text("not json")
        with self.assertRaisesRegex(ValueError, "--authorize"):
            load_credentials(self.client, self.token)

    def test_explicit_authorization_opens_browser_and_saves_private_token(self):
        self.client.write_text("{}")
        with patch("google_calendar.InstalledAppFlow") as flow:
            flow.from_client_secrets_file.return_value.run_local_server.return_value = credentials()
            load_credentials(self.client, self.token, authorize=True)
            flow.from_client_secrets_file.assert_called_once_with(str(self.client), SCOPES)
            options = flow.from_client_secrets_file.return_value.run_local_server.call_args.kwargs
            self.assertEqual(options["port"], 0)
            self.assertEqual(options["authorization_prompt_message"], "")
            self.assertEqual(options["prompt"], "consent")
        self.assertEqual(self.token.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.token.parent.stat().st_mode & 0o777, 0o700)

    def test_failed_token_write_preserves_previous_token(self):
        self.write_token(credentials())
        before = self.token.read_text()
        with patch("google_calendar.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(ValueError, "save"):
                google_calendar.save_token(self.token, credentials())
        self.assertEqual(self.token.read_text(), before)
        self.assertEqual(list(self.token.parent.iterdir()), [self.token])


if __name__ == "__main__":
    unittest.main()
