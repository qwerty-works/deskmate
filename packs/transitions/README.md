# Color Current — AWTRIX Transition Pack

Color Current is a set of three original full-screen interludes for AWTRIX NG's 32 × 8 display. Aurora gradients, rolling ocean ripples, and woven prism curtains fill all 256 pixels in every animation frame.

The Berry scripts run between widget apps as interludes. They do not replace the firmware's native transition effects. Aurora Tide and Prism Loom default to three seconds; Ocean Drops defaults to five seconds. Each supports a configurable duration from one to five seconds.

## Pack contents

- `aurora-tide.be` — a teal-to-coral aurora wave wipe.
- `ocean-drops.be` — layered, expanding ocean rings and a moving crest.
- `prism-loom.be` — sliding color curtains with a bright weaving seam.
- `manifest.json` — animation metadata for the pack.
- `previews/*.png` — cover frames captured from the AWTRIX NG device.
- `previews/*.gif` — short animated captures from the AWTRIX NG device.
- `tools/render.py` — renderer and packager; running it creates GIF/PNG previews, an offline gallery, and the ZIP bundle.

## AWTRIX Hub

- [Aurora Tide](https://awtrix.de/flow/9tbUOBFb3sSR)
- [Ocean Drops](https://awtrix.de/flow/QVamcPqYPPwh)
- [Prism Loom](https://awtrix.de/flow/kpvjzu2GZlqv)

## Install on AWTRIX NG

1. Open the device settings and choose **Scripts**.
2. Choose **Import**, select one `.be` script, then choose **Save**.
3. Repeat for the other scripts. Use **Show on AWTRIX** to preview an animation.
4. Add the saved scripts to the app rotation on the **Apps** page if you want them to play between widgets.

The script files are also usable individually without the preview tooling.

## Build previews and the ZIP

The build tool uses the Berry interpreter and Pillow. From the repository root, run:

```sh
python3 packs/transitions/tools/render.py --berry /path/to/berry
```

The renderer checks source lifecycle and duration behavior, 200 sampled frames, full 256-pixel color coverage on every frame, color variation, and the five-second GIF timing before it writes the previews, manifest, gallery, and ZIP.

## Compatibility note

The host renderer validates Berry behavior and preview output. It does not emulate device brightness, panel color calibration, or the app-rotation settings. Check the animations on your clock after importing them.

## Credits and license

Animations and artwork are original to this pack. Distributed under the MIT License; see `LICENSE`.
