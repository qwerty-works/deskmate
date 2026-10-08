---
name: deskmate-awtrix-packs
description: Author, render, package, or schedule Desk Mate AWTRIX Berry animation packs and idle-mode transitions with device-safe state restoration.
---

# Desk Mate AWTRIX packs and idle mode

Use this skill for `packs/`, Berry scripts, `src/idle_mode.py`, or the
associated render/test workflow.

## Animation and pack contract

- Berry animations target the 32x8 display. Use the pack's existing renderer
  (`packs/halloween/tools/render.py` or `packs/transitions/tools/render.py`)
  and its `build()` checks rather than hand-editing generated previews or ZIPs.
- A valid build verifies Berry execution, lifecycle/config behavior, 200 frames,
  256-pixel RGB bounds, meaningful motion/color variation, GIF pixel parity, the
  animation's registered cycle, gallery/contact sheet output, manifest metadata,
  and a reproducible ZIP. Preserve the pack's stricter full-panel-color checks
  where they already apply.
- `great-wave.be` is also consumed at runtime by `src/meeting_mode.py`, which
  installs it as the `deskmate-wave` app during calendar meetings. Its 7000 ms
  default, its 1000–7000 clamp, and its seamless cycle are a product contract
  for that path, not only a preview concern, so treat a change to any of them as
  a behavior change for the meeting display.
- Keep source `.be`, previews, manifest, README/license, and ZIP contents
  coherent. Generated artifacts are outputs of the renderer, not independent
  sources of truth.

## Idle-mode safety

- `idle_mode.py` is a reversible controller, not a replacement animation
  installer. It must preserve the original AWTRIX `Pixel-Fireplace` script;
  refuse a non-script collision and refuse to substitute a bundled animation
  when the original script is absent.
- On entry, snapshot brightness, auto-brightness, app order, disabled apps, and
  the active app in the private state file. Use the configured timezone and
  brightness bounds, then verify the script is present, enabled, and inLoop.
- On exit, restore the saved settings/order/active app, remove only the idle
  app, and remove the state file. Keep operations idempotent and preserve
  unrelated apps.
- Use the existing `enter`, `exit`, and `sync` commands with separate Pi
  locking/logging; test midnight boundaries and state restoration.

Run the focused pack/idle tests and renderer build before claiming a visual
change is valid. A generated GIF or local test does not prove the physical
AWTRIX display; device readback or an explicitly reported visual limitation is
still required.
