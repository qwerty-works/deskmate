---
name: deskmate-awtrix-hub-publishing
description: Use when publishing a Desk Mate Berry animation or script to AWTRIX Hub, especially when a public listing needs source code, metadata, and an animation preview verified together.
---

# Desk Mate AWTRIX Hub publishing

Use this after the animation has passed the local pack checks. AWTRIX Hub's
Berry animation is a public AWTRIX NG script listing even when its resulting
URL contains `/flow/`.

## Prepare the listing

- Publish the `.be` source as a script, not an unrelated Home Assistant or
  Node-RED flow. Select the Animations topic and AWTRIX NG compatibility.
- Use the animation's real name, a short behavior-focused description, and
  setup text that states display size, dependencies, duration/configuration,
  and installation/rotation expectations.
- Provide the generated GIF (or a native-size screenshot when a GIF is not
  appropriate) as the cover. Respect the Hub's visible format, duration, and
  size limits.

## Required verification before publishing

- The upload control showing `skulls-in-space.be` is not enough: verify the
  actual Code editor contains the full Berry source. File selection can update
  only the filename label while leaving the editor empty.
- Verify the cover list contains the intended preview and the listing card
  visibly shows the animation. Check the source and preview are from the same
  revision.
- Stage the complete form and stop at the final Publish button. Public
  publication is an external representational action; ask for confirmation
  immediately before clicking it, even if the user earlier requested
  publication.

## After publication

- Verify the resulting public URL, title, author, topic, AWTRIX NG status,
  download/code availability, and cover image. Do not infer a URL from a
  guessed slug.
- Report publication separately from device installation or preview. A public
  Hub page does not prove the animation is active on hardware.
- Publish individual entries deliberately; do not automate bulk submissions or
  repeated Publish clicks. If the site rate-limits or loses the staged form,
  stop and reconcile before retrying.
