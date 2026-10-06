---
name: deskmate-awtrix-widgets
description: Build or change Desk Mate AWTRIX widgets and pushed apps while preserving device state, app ownership, and readback verification.
---

# Desk Mate AWTRIX widgets

Use this skill for changes to `src/awtrix.py`, `src/main.py`, `src/codex.py`,
`src/calendar_widget.py`, or another integration that pushes an AWTRIX app.

## Project contract

- Reuse `src/awtrix.py`; do not create a second HTTP client. It validates the
  base URL, bypasses shell proxies for LAN access, sends JSON for pushed apps,
  and rejects malformed/non-2xx responses.
- Before changing a named app, call `GET /api/v1/apps`. Refuse to replace or
  delete an app whose `origin` is not the kind the integration owns. A request
  acknowledgment is not completion: verify the replacement is `present`,
  `enabled`, and `inLoop`.
- Preserve unrelated apps. Retire legacy pushed pages only after the new page
  has passed readback verification, and verify again after cleanup.
- Provider failure, malformed data, stale data, or an AWTRIX failure is an
  error. Do not turn an unknown/error state into a blank or reassuring display.
- Keep display semantics explicit. For Codex, render remaining allowance (not
  used percentage), use the official app-server `account/rateLimits/read`
  data, and retain the 32x8 RGB888 bitmap contract. For other widgets, encode
  the user-visible meaning in tests before changing layout or labels.
- Keep logs useful but non-sensitive. Do not echo OAuth tokens, credentials,
  provider bodies, or private calendar titles into application logs.

## Development loop

1. Use `graft ask` or `graft callers` to locate the integration and its tests.
2. Add focused tests for validation, collision safety, payload shape, and
   post-write readback before touching live hardware.
3. Run the focused tests, then `python -m unittest discover -s tests -v` and
   `git diff --check` when the change is complete.
4. If live verification is requested, record the actual endpoint, HTTP result,
   app flags, and any remaining unverified physical-display behavior.

Do not claim that a passing unit test proves the AWTRIX device changed; device
readback is the evidence for that boundary.
