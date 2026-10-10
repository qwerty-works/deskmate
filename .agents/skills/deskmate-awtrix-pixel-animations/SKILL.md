---
name: deskmate-awtrix-pixel-animations
description: Use when designing or revising Desk Mate AWTRIX Berry animations where 32x8 pixel density, readable silhouettes, depth, or motion speed must be judged on the actual display grid.
---

# Desk Mate AWTRIX pixel animations

Use this alongside `deskmate-awtrix-packs` for creative animation changes. The
pixel grid is the design surface: do not rely on antialiasing, subpixel motion,
or a large preview to make an ambiguous sprite readable.

## Design contract

- Start from the target device dimensions, normally 32x8. Inspect representative
  frames at native grid size before judging the animation.
- Keep an empty black background when the brief calls for space. Do not add
  decorative stars unless requested; a requested distant skull may be one dim
  pixel.
- A readable skull has two black eye sockets, a 50%-white nose pixel, and three
  black mouth pixels. No eye glow, colored eyes, or facial detail that collapses
  at native resolution.
- Use stepped, integer-pixel silhouettes. Scale features with the sprite: a
  small skull may simplify its outline, but it must still be distinguishable as
  a skull rather than a blob.
- Create depth with three coordinated signals: smaller sprites are dimmer,
  smaller sprites move more slowly, and foreground sprites are larger/brighter
  and move faster. Keep enough separation that overlapping sprites remain
  discernible.
- Limit simultaneous elements. Favor a few clearly readable skulls over a busy
  field; validate edge entry/exit and the most crowded frame.

## Validation

1. Render with the pack renderer; the `.be` source remains authoritative.
2. Sample native 32x8 frames, including the densest frame, and verify every
   skull tier and the single-pixel distant markers are visible.
3. Check that the animation moves left-to-right, foreground motion is faster,
   and brightness decreases with distance. Confirm there are no glowing eyes or
   unintended background pixels.
4. Run the focused renderer/tests and, when a device is in scope, read back the
   AWTRIX framebuffer. A GIF preview proves the artifact, not the physical
   display.
