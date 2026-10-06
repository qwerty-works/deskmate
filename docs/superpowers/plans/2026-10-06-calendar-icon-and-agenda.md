# Calendar Icon + Multi-Event Agenda Implementation Plan

Supersedes `2026-10-06-meeting-in-progress-icon.md` (see "Corrections" below).
Goal: the `google_calendar` page carries the device-resident `calendardots` icon
on **every** payload, and shows **several** eligible events per push instead of
exactly one, so the display is never blank while real events exist.

## Established facts (verified against the live clock on 2026-10-06, not assumed)

- `GET http://192.168.4.94/api/v1/files?dir=/ICONS` returns
  `{"files": [{"name": "calendardots.gif", "size": 146}], "usedBytes": 90112, "totalBytes": 524288}`.
  `GET /ICONS/calendardots.gif` returns **200**, 146 bytes, magic `GIF89a`, 8×8.
  The icon is **already installed on the physical device**, so AWTRIX's documented
  icon-ID resolution (`/ICONS/<id>.gif` then `/ICONS/<id>.jpg`, for `icon` values
  ≤ 64 chars) will render `icon: "calendardots"`. Reference:
  <https://blueforcer.github.io/awtrix-ng/reference/payload/#icon>.
- Device setting `uppercase` is **`false`**. The superseded plan claimed `text`
  would render as `MEETING IN PROGRESS`; it will render lowercase as sent. Do not
  change this device setting either way.
- Live `GET /api/v1/apps` shows `google_calendar` as
  `{"enabled": true, "inLoop": false, "present": false, "origin": null}`.
  The page is **not present and not in the rotation**. `calendar_widget.run()`
  requires `present`+`enabled`+`inLoop` after every push and raises otherwise
  (`src/calendar_widget.py:76-79`), so while the device reports `inLoop: false`
  every cron run fails its own readback. This is a live availability defect
  independent of the icon work.
- `src/google_calendar.py:143-171` `select_event` returns **one** event or `None`;
  `fetch_events` (`:91-133`) already pages correctly and never degrades to empty.
- `src/google_calendar.py:174-201` `event_payload` returns the whole payload dict;
  the in-progress branch is `:179-181`, text `In progress ` + title.
- Upcoming branch `:182-194` builds `Today`/`Tomorrow <clock>`/`<Mon D> <clock>` text.
- Payload cap is 8192 bytes (`413 payloadTooLarge`); the existing payload is
  ~250 bytes, so a multi-event string is nowhere near it.
- `iconMode` defaults to `fixed`, so the icon holds position while text scrolls
  behind the gap. Do not set `iconMode` explicitly.
- Device is on `gitbutler/workspace` at `6a288be` with uncommitted
  `opencode.json` and the superseded plan doc. Work happens in separate worktrees.

## Corrections to the superseded plan

1. Its "blocking prerequisite (human, not an agent)" — download the GIF from a
   signed-in awtrix.de account — is **resolved**. The icon is on the device, and
   the user chose device-name resolution over an inline base64 asset.
2. Its out-of-scope list excluded icon-name references because `/ICONS` was
   empty at the time. That is no longer true, so icon-name reference is now the
   chosen design.
3. Its `assets/calendardots.gif` loader, base64 size guard, and non-GIF rejection
   are **dropped** — no repo asset is vendored. Remove those checklist items.
4. Accepted risk of icon-name reference: if `/ICONS` is ever cleared, AWTRIX
   silently falls back to the icon-less layout. Documented behavior, not an error.
   This is the deliberate tradeoff the user chose.

## Workstream A — calendardots icon

Files: `src/google_calendar.py`, `tests/test_google_calendar.py`.

- [ ] `event_payload` gains a module-level `CALENDAR_ICON = "calendardots"` and
      returns `icon: CALENDAR_ICON` on **both** branches — underway and upcoming.
      No other key changes.
- [ ] In-progress `text` becomes exactly `meeting in progress` (title dropped, per
      the superseded plan's decision).
- [ ] Do not set `iconMode`. Do not touch device settings.
- [ ] `scroll`, `repeat: 1`, `lifetimeMs` (≤ 120 s, capped at the event boundary)
      and `lifetimeExpiry: "remove"` stay byte-identical. The expiry contract must
      not regress: the page still removes itself at the meeting end.
- [ ] Tests: assert `icon` on the underway and upcoming payloads; assert
      `text == "meeting in progress"`. Replace the `In progress` assertions at
      `tests/test_google_calendar.py:57` and `:114`.

## Workstream B — multi-event agenda

Files: `src/google_calendar.py`, `src/calendar_widget.py`, both test files.

- [ ] Rename `select_event` → `select_events(events, now, limit=3)`, returning a
      `list[CalendarEvent]` ordered ongoing-first then earliest-start-first. Reuse
      the existing per-event validation verbatim (skip cancelled, self-declined,
      all-day; reject malformed timed events; compare in UTC). `limit` clamps to
      at least 1.
- [ ] Keep the 24-hour exclusive horizon and all of `fetch_events` unchanged.
- [ ] `event_payload` takes the list and composes one scrolling line:
      - ongoing present → `meeting in progress`
      - each upcoming event → its existing local-time form
        (`2:30 PM Team sync` / `Tomorrow 9:00 AM Standup` / `Oct 12 3:00 PM Offsite`)
      - joined with `" | "` (ASCII; the matrix font has no safe middle dot)
      - `icon` is `calendardots` from Workstream A.
- [ ] `lifetimeMs` = `min(120 s, time to the earliest start/end transition among
      the shown events)` — unchanged rule, now evaluated across the list.
- [ ] `calendar_widget.run` passes the list; the hide-when-clear branch now hides
      only when the list is **empty**, and still verifies removal.
- [ ] Keep the no-titles-in-logs rule and every error path: auth, network,
      malformed-response and AWTRIX failures must still raise and must never
      delete or blank the existing page.

## Workstream C — availability diagnosis (no code unless proven)

- [ ] Determine why the device reports `inLoop: false` for `google_calendar` while
      the widget's own readback requires `true`. Check whether the Pi cron entry
      exists and what `calendar.log` actually says.
- [ ] This is diagnosis first. Change code only if a code defect is proven, and
      report the evidence either way.
- [ ] **Never** flip a device app's `enabled`/`inLoop`/`order` flags to make a
      verification pass. Report the state and let the user decide.

## Cross-cutting

- [ ] `docs/google-calendar.md`: display table (rows ~8-11), prose (~175), and add
      the multi-event format plus the icon-name reference and its silent-fallback risk.
- [ ] `README.md:7`: `In progress` → `meeting in progress`; note several events.
- [ ] `.agents/skills/deskmate-google-calendar/SKILL.md`: update the
      "Fixed product behavior" render bullet and the Verification note.
- [ ] `graft build`, then `python -m unittest discover -s tests -v` must be green.

## Acceptance

- Every `google_calendar` payload carries `icon: "calendardots"`.
- Underway push: `text == "meeting in progress"`, icon present, expiry still lands
  on the event end at the 120 s cap.
- Upcoming push: up to 3 events, `" | "`-joined, each with its correct local-time
  form across today / tomorrow / day-after and across DST boundaries.
- An empty eligible list still hides the page and verifies removal.
- All four test modules green; `graft build` clean.

## Explicitly out of scope

- Vendoring the GIF into `assets/` or inlining base64 — superseded, icon resolves
  on the device.
- Device `/ICONS` upload (`PUT /api/v1/files`) — device state this project does
  not manage.
- A Berry script with `# @icons calendardots` — would replace the pushed-app and
  expiry design.
- Changing device `uppercase`, `scroll`, `iconMode`, or app flags.
- Multi-day horizons beyond 24 h — the user chose "more events", not "wider window".

## Unverifiable without hardware

Icon legibility at 8×8 beside a long scrolling line on a 32×8 panel, animation
playback, and whether AWTRIX renders `" | "` separators cleanly need the TC001.
Tests prove the payload shape only.