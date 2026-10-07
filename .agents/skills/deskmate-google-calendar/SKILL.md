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
  Skip all-day, cancelled, and self-declined events. `select_events(events, now,
  limit=3)` returns a list of eligible `CalendarEvent` objects ordered
  ongoing-first then earliest-start-first; `limit` clamps to at least 1.
- While ANY selected event is ongoing, hand the display to the Great Wave
  animation exclusively (`deskmate-wave`, driven by `src/meeting_mode.py`) and
  push no text page for that run. This supersedes the agenda's
  `meeting in progress` line: `event_payload` still builds that marker and still
  has unit tests, but the widget no longer pushes a page during a meeting, so it
  is unreachable through the display. The takeover is poll-driven by the
  once-a-minute run, so it can outlive a meeting by up to one minute, and
  `meeting_mode.py exit` is the documented recovery. Release it on the first run
  with nothing ongoing -- including the emptied-calendar branch, which must not
  strand the wave -- and restore the snapshotted app order, disabled apps, and
  brightness.
- Otherwise render one scrolling agenda line. Set `icon` to `calendardots` by
  name on every payload; it resolves on the device from
  `/ICONS/calendardots.gif`, and no GIF is vendored in this repo. Render each
  upcoming event as local time plus title with `Tomorrow` or month/day when
  needed, and join the entries with the literal `" | "`. Hide the
  `google_calendar` app when the selected list is empty.
- Set scrolling payload expiry no later than the soonest start/end transition
  among the shown events and at most two minutes. A no-event result is valid
  only after a successful, complete fetch; auth, network, malformed-response,
  and AWTRIX failures must leave existing display content alone and return an
  error.

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
regressions. Tests prove the payload shape only: `icon == "calendardots"`, the
`" | "`-joined agenda, and that an ongoing event hands the display to the wave
instead of pushing a page. They do not prove icon legibility at 8×8 beside a long
scrolling line, wave animation playback, or how AWTRIX renders the `" | "`
separator — confirm those on the physical TC001. A real Pi run with no eligible
event proves fetch/deployment and hide behavior, but not physical readability;
report that distinction.

## Plan history

`docs/superpowers/plans/2026-10-07-meeting-wave-animation.md` supersedes the
`meeting in progress` display row from
`docs/superpowers/plans/2026-10-06-calendar-icon-and-agenda.md`, which itself
supersedes `2026-10-06-meeting-in-progress-icon.md`.
