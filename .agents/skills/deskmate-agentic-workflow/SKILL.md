---
name: deskmate-agentic-workflow
description: Plan and execute Desk Mate changes with bounded sub-agent ownership, isolated worktrees, independent review, and verified Git integration.
---

# Desk Mate agentic workflow

Use this skill when a Desk Mate task benefits from multiple agents, isolated
changes, or a reviewable PR. Keep the team small and make one root orchestrator
accountable for the integrated result.

## Team contract

The root orchestrator owns the requirements, scope decisions, shared
interfaces, worktree setup, integration order, final verification, PR, and
merge. Worker agents return evidence and commit only the files they own.

Use these roles only when they add real value:

- **Explorer:** read-only repository and runtime discovery; no edits.
- **Implementation worker:** one bounded behavior or documentation surface.
- **Specialist reviewer:** read-only review for correctness, security, tests, or
  device/runtime boundaries.
- **Integration owner:** reconciles approved commits and owns the final branch.

Every worker handoff must state its branch, changed files, tests run, known
limitations, and the commit or worktree location.

## Planning and ownership

Before editing, inspect `AGENTS.md`, the repository graph, current Git state,
dirty files, worktrees, and available test commands. Preserve unrelated
user changes. Decompose the task into 2–4 meaningful streams and record, for
each stream, its inputs, exact owned paths, prohibited paths, dependencies,
acceptance criteria, and verification command.

Give each independent tracked stream its own worktree and short-lived branch.
Do not let two workers write the same tracked file. Serialize shared schemas,
generated outputs, migrations, device state, deployment, and destructive
operations behind the orchestrator.

Do not copy secrets, private credentials, production data, or bulky ignored
artifacts into a worktree. If the primary checkout contains unrelated dirty
changes, integrate from a clean dedicated checkout instead of resetting,
stashing, or discarding those changes.

## Execution gates

1. Establish the base commit and worktree map before starting workers.
2. Run independent workers in parallel only when their ownership is disjoint.
3. Review each worker's diff and tests before integration; do not rely on its
   summary alone.
4. Run an independent read-only review of the combined result and require an
   explicit approval before publication.
5. Run focused checks, the project's relevant full test suite, and whitespace
   validation before committing or opening a PR.
6. Use the repository's standard Git workflow for branches, commits, pushes,
PRs, and history operations. Publish only with explicit user authorization.
7. Verify the PR diff and required checks, merge only the intended branch, then
   confirm the merged commit is on the target branch. Report any runtime,
   device, or deployment boundary that was not verified.

## Scope and safety

Do not broaden a cleanup into an unrelated refactor. Do not remove a legacy
file, branch, worktree, app, schedule, or device setting unless its ownership
and replacement are proven. Treat timeouts and lost responses as unknown until
reconciled, and never retry a non-idempotent external effect blindly.
