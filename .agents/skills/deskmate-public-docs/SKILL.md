---
name: deskmate-public-docs
description: Audit and publish Desk Mate README and integration documentation for privacy, accuracy, generic setup, and narrowly scoped version-control delivery.
---

# Desk Mate public documentation

Use this skill for README, `docs/`, release notes, community-pack descriptions,
or documentation-only publication.

## Audit boundaries

- Treat public docs and source defaults as separate findings. Replace personal
  LAN addresses, usernames, machine paths, credential-shaped values, and
  private examples in public docs with generic placeholders, but report source
  fallbacks separately instead of silently expanding a docs-only change.
- Keep the primary setup generic for community users. Raspberry Pi, SSH, OAuth,
  and personal-device details belong in clearly optional sections with
  placeholder paths/hosts.
- Documentation must match actual behavior: read-only Calendar scope,
  hide-when-clear semantics, AWTRIX ownership/readback checks, optional Pi
  scheduling, and the original Pixel-Fireplace preservation rule.
- Explain that calendar titles appear on the physical display, secrets remain
  local and ignored, and AWTRIX is a privileged local control plane.

## Publication gate

1. Inspect the current workspace and limit the diff to approved documentation
   files; preserve unrelated branches, configuration, and dirty work.
2. Run `git diff --check` and the relevant documentation/tests or link checks.
3. Obtain an independent read-only review with an explicit `APPROVE` verdict
   before committing or pushing docs changes when publication is requested.
4. Use GitButler for the scoped commit/push. Record the exact files and any
   source-default findings left outside scope.

Never claim that a clean docs scan proves the entire repository contains no
private-looking values, and never delete an unmerged branch during cleanup
without explicit confirmation.
