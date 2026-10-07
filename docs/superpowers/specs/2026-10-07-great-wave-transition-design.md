# Great Wave Transition Animation Design

## Goal

Add one original AWTRIX NG transition animation to the existing `packs/transitions` pack. The animation will evoke the composition and palette of Hokusai's *Under the Wave off Kanagawa* without reproducing the source artwork: a large curling wave crest, layered blue water, pale foam, and a restrained warm accent.

## Scope

- Add `packs/transitions/great-wave.be`.
- Register the animation in `packs/transitions/tools/render.py`.
- Regenerate the existing gallery, manifest, contact sheet, previews, and reproducible ZIP through the renderer.
- Keep the existing pack name, naming conventions, and duration configuration pattern unchanged. Existing animations retain their current durations; Great Wave adds a 7000 ms default within the renderer's per-animation duration support.
- Do not install or activate the animation on a physical AWTRIX device as part of this change.

## Visual and motion design

The animation renders every pixel of the 32×8 panel on every frame. A deep indigo base carries a cobalt-to-teal water gradient. A parametrically shaped crest travels across the panel, with a hooked leading edge and broken pale foam highlights that suggest the claw-like silhouette of a great wave at pixel scale.

The palette is intentionally limited and woodblock-like: midnight navy, indigo, cobalt, sea teal, seafoam, and a small warm cream/gold highlight. The effect is original pixel art rather than a literal reconstruction or traced image.

The script uses the existing `durationMs` configuration, clamped to 1000–7000 ms with a 7000 ms default, resets its phase in `on_show()`, and derives motion from `now_ms()` so variable frame timing does not drift. All moving geometry is driven by periodic phase functions; there is no one-way fade or edge state. At exactly one duration after the start, the rendered frame must equal the initial frame, making the animation loop seamlessly.

## Architecture and data flow

`great-wave.be` follows the same self-contained Berry app shape as the existing transitions:

1. `init()` initializes the start time and configured duration.
2. `duration()` reads and clamps `durationMs`.
3. `on_show()` restarts the animation phase whenever rotation selects it.
4. `draw()` computes normalized periodic phase, the traveling crest geometry, foam bands, and per-pixel color, then writes the 32×8 frame.

The renderer discovers the source through `NAMES`, `DEFAULT_DURATIONS`, and a per-animation duration map, executes it with the existing Berry prelude, samples 200 frames, and creates all derived artifacts. Its GIF timing and pixel-parity assertion must use the registered duration rather than a pack-wide 5000 ms constant. No new device API is needed.

## Error handling and constraints

- Berry source must use only APIs already supported by the transition renderer and AWTRIX reference.
- Every pixel must remain within RGB bounds and nonzero because this pack requires a full-panel undercurrent.
- The source must remain small enough for the shared Berry heap; use a few methods and arithmetic rather than frame arrays or uploaded icons.
- Invalid duration settings must fall back through the existing clamp behavior, with Great Wave's upper bound at 7000 ms.
- The renderer must verify the Great Wave seam by rendering at `t=0` and exactly one configured duration later and asserting identical 256-pixel frames.
- A renderer or Berry failure must stop the build rather than emitting partially trusted artifacts.

## Verification

Run the existing transitions renderer with the project Berry interpreter. Its build must prove:

- source compiles and lifecycle/configuration checks pass;
- 200 frames render at 32×8 with valid RGB integers;
- at least 15 distinct frames and at least 8 colors exist;
- all 256 pixels are nonzero on every sampled frame;
- each generated GIF has pixel parity and its registered exact cycle length, including Great Wave at 7000 ms;
- Great Wave's first and end-of-cycle frames are identical;
- gallery, manifest, contact sheet, previews, and ZIP include the new animation.

Review the generated GIF/contact sheet for the intended curling crest and readable motion. Physical AWTRIX display behavior remains a separate device-level verification boundary.
