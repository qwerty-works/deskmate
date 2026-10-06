---
name: deskmate-pi-operations
description: Deploy, schedule, and diagnose Desk Mate on a Raspberry Pi without moving credentials or breaking existing widget schedules.
---

# Desk Mate Raspberry Pi operations

Use this skill for Pi deployment, cron changes, SSH-backed Codex reads, or
runtime diagnosis. Reinspect the actual checkout, branch, environment, and
device reachability before acting; remembered hostnames and paths are examples,
not current authorization.

## Runtime topology

- The Pi is the scheduler and AWTRIX/LAN runtime. When `CODEX_SSH_HOST` is set,
  the Mac owns the Codex CLI, `CODEX_HOME`, login state, and account data; do
  not copy Codex credentials or transcripts to the Pi.
- Use the repository virtualenv and explicit absolute paths in cron. Keep the
  Codex, Calendar, and idle-mode jobs separate, each with its own `flock` lock
  and log file. Never replace an existing crontab wholesale.
- Normal jobs must work in cron's minimal environment: load `.env` deliberately,
  use bounded timeouts, and make browser authorization an explicit one-time
  Mac operation rather than a cron fallback.

## Safe deployment loop

1. Confirm the target checkout and current files before copying or installing.
2. Run the relevant local tests and inspect the intended diff.
3. Deploy code plus required dependency metadata, then verify the Pi virtualenv
   has no broken requirements.
4. Run the exact command once under a cron-like environment, inspect its log and
   exit status, and verify the AWTRIX state when the run should write it.
5. For SSH-backed Codex reads, verify Mac Remote Login, key authorization, host
   key, reachability, and the noninteractive command before diagnosing provider
   data.

Do not call a deployment complete because files copied successfully. The
runtime command, lock/log behavior, and relevant device readback must be
verified; if no Calendar event exists, say that physical active-event rendering
remains unverified.
