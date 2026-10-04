# Halloween Spooky Pack Implementation Plan

Approved design: six playfully spooky, standalone Berry interlude apps for AWTRIX NG on a 32×8 TC001. The user increased the default duration to five seconds; duration remains configurable from one to five seconds.

## Implementation

- [x] Delegate three independent script pairs with a shared palette and duration contract.
- [x] Implement bats/ghost, pumpkin/slime, and spiders/eyes in `packs/halloween/`.
- [x] Run original scripts through a real Berry interpreter and clipped drawing adapter.
- [x] Produce a replay gallery, GIFs, posters, manifest, and ZIP.
- [x] Document installation, interlude placement, duration, native transition timing, removal, and community sharing.
- [x] Complete GIF decode parity verification and integration review.
- [x] Verify existing repository tests with the project virtual environment.

## Acceptance

Scripts default to 5000ms, clamp numeric duration to 1000–5000ms, reset at every on_show, use no downloaded resources, preserve button navigation, and never mutate device settings. GIFs run for exactly 5000ms and match Berry-rendered pixels. The gallery supports pause/play/replay and script/bundle downloads. Original code and art ship with an MIT license.

Device installation, live rotation, reboot persistence, brightness, and readability need a physical TC001 and remain explicitly unverified. No public upload is part of this delivery. GitButler database access requires execution outside the filesystem sandbox; save only this pack and its plan on a dedicated branch, preserving unrelated work.
