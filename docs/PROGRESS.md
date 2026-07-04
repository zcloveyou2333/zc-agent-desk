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

- Candidate installed from a manually downloaded GitHub source archive: Hermes
  `0.18.0`. Because an archive has no Git metadata, three critical file hashes
  are recorded in `config/hermes-source.lock` instead of inventing a commit.
- Hermes requires both `HERMES_ENABLE_PROJECT_PLUGINS=1` and an explicit
  `plugins.enabled` entry. The config template now records both requirements.
- Hermes 0.18.0 also requires `API_SERVER_KEY` for loopback-only API serving.
  The project-level `HERMES_API_KEY` will be mapped to that native variable.
- Under the macOS policy, `/health`, `/v1/models`, and `/v1/capabilities`
  returned HTTP 200; `/v1/runs` created a run and its SSE endpoint returned a
  terminal `run.failed` event correctly.
- The configured upstream first timed out and then rejected the model request
  with HTTP 401. A direct provider probe also timed out. Structured tool calls
  and blocking approval remain unverified until a working provider token is
  supplied.

## Next action

User updates `OPENAI_API_KEY` to a currently valid provider token and generates
`HERMES_API_KEY` with `openssl rand -hex 32`. Resume G1 with live text,
structured-tool, and blocking-approval probes. Do not start G2 before this gate
is resolved.

## Recovery protocol

1. Read `docs/PROGRESS.md` and `docs/DECISIONS.md`.
2. Run `git status --short --branch` and inspect the last commit.
3. Run the verification command recorded for the active gate.
4. Continue only the active gate; do not start later work with an unverified
   working tree.
