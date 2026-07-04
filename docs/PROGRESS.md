# Progress and Recovery

## Current gate

G1 - Hermes feasibility, blocked pending user approval/resources.

## Completed

- Scope and architecture approved.
- Product name fixed as ZC Agent Desk, built by zcloveyou.
- Design, decisions, AI collaboration format, and recovery record created.
- Project plugin contract tests pass for the two business tool schemas.
- Hermes project-plugin discovery was verified with an isolated `HERMES_HOME`.
- macOS `sandbox-exec` probe permits workspace writes and denies `/tmp` writes
  plus reads under `~/.ssh`.

## G1 evidence and blockers

- Candidate inspected offline: Hermes `70b663504fee1d58a6763e862df478cf101fe51e`
  (`0.13.0`, dated 2026-05-16).
- The remote `main` hash observed during planning was newer, but two fresh
  shallow-clone attempts created no usable `HEAD`. The latest source is not yet
  verified.
- Hermes requires both `HERMES_ENABLE_PROJECT_PLUGINS=1` and an explicit
  `plugins.enabled` entry. The config template now records both requirements.
- `.env` is absent, so live text generation, structured tool calls, run SSE,
  and blocking approval have not been tested.

## Next action

User chooses whether to retry latest upstream or temporarily pin the inspected
commit, then creates `.env` from `.env.example`. Resume G1 by installing the
pinned Hermes candidate and running live health, run/event, structured-tool,
and blocking-approval probes. Do not start G2 before this gate is resolved.

## Recovery protocol

1. Read `docs/PROGRESS.md` and `docs/DECISIONS.md`.
2. Run `git status --short --branch` and inspect the last commit.
3. Run the verification command recorded for the active gate.
4. Continue only the active gate; do not start later work with an unverified
   working tree.
