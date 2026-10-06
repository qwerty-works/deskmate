---
name: deskmate-google-calendar
description: Maintain Desk Mate's read-only Google Calendar widget, including OAuth, event selection, timezone behavior, AWTRIX expiry, and unattended Pi execution.
---

# Desk Mate Google Calendar

Use this skill for `src/google_calendar.py`, `src/calendar_widget.py`, their
tests, or the Calendar setup documentation.

## Fixed product behavior

- The source is the user's `primary` calendar and the scope is
  `calendar.events.readonly`; the integration never creates, edits, or deletes
  calendar events.
- Fetch a 24-hour exclusive horizon with `singleEvents=True` and
  `orderBy="startTime"`, follow every page, and compare event times in UTC.
  Skip all-day, cancelled, and self-declined events. Select the earliest
  ongoing event, otherwise the earliest upcoming eligible event.
- Render an ongoing event as `In progress <title>`. Render an upcoming event
  as local time plus title, with `Tomorrow` or month/day when needed. Hide the
  `google_calendar` app when there is no eligible event.
- Set scrolling payload expiry no later than the next event transition and at
  most two minutes. A no-event result is valid only after a successful,
  complete fetch; auth, network, malformed-response, and AWTRIX failures must
  leave existing display content alone and return an error.

## Security and operations

- `--authorize` is the only browser-auth path and is intended for the Mac.
  Normal Pi/cron runs are noninteractive and only load/refresh an existing
  token.
- Store credentials/tokens under a mode-`700` directory with token files mode
  `600`, using atomic replacement. Never log or paste client secrets, refresh
  tokens, access tokens, OAuth URLs, or event titles.
- Before changing `google_calendar`, reject a non-pushed name collision. After
  a push, verify `present`, `origin=pushed`, `enabled`, and `inLoop`.
- Preserve the separate Calendar lock/log and existing Codex schedule when
  documenting or installing Pi cron entries.

## Verification

Use `tests/test_google_calendar.py` and `tests/test_calendar_widget.py` as the
contract. Include pagination, DST boundaries, invalid provider responses,
token permissions, collision safety, expiry, and hide-when-clear cases in
regressions. A real Pi run with no eligible event proves fetch/deployment and
hide behavior, but does not prove physical scrolling or `In progress` display
readability; report that distinction.
