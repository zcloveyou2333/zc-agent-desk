# Progress and Recovery

## Current gate

G1 - Hermes feasibility complete; awaiting user approval to start G2.

## Completed

- Scope and architecture approved.
- Product name fixed as ZC Agent Desk, built by zcloveyou.
- Design, decisions, AI collaboration format, and recovery record created.
- Project plugin contract tests pass for the two business tool schemas.
- Hermes project-plugin discovery was verified with an isolated `HERMES_HOME`.
- macOS `sandbox-exec` probe permits workspace writes and denies `/tmp` writes
  plus reads under `~/.ssh`.
- Live relay text, explicit conversation history, structured tool calls, SSE,
  and blocking approval denial have been verified through Hermes `/v1/runs`.

## G1 evidence and blockers

- Candidate installed from a manually downloaded GitHub source archive: Hermes
  `0.18.0`. Because an archive has no Git metadata, three critical file hashes
  are recorded in `config/hermes-source.lock` instead of inventing a commit.
- Hermes requires both `HERMES_ENABLE_PROJECT_PLUGINS=1` and an explicit
  `plugins.enabled` entry. The config template now records both requirements.
- Hermes 0.18.0 also requires `API_SERVER_KEY` for loopback-only API serving.
  The project-level `HERMES_API_KEY` will be mapped to that native variable.
- Under the macOS policy, `/health`, `/v1/models`, and `/v1/capabilities`
  returned HTTP 200. A text run streamed `连接成功`, and explicit history
  correctly recovered the test code `雁七`.
- Hermes intentionally refuses to forward the generic `OPENAI_API_KEY` to a
  bare custom third-party host. The config now selects `custom:zc-relay` and
  binds `key_env: OPENAI_API_KEY`; no credential is stored in the config.
- The model autonomously called `query_mock_business`; Hermes emitted ordered
  `tool.started`, `tool.completed`, message delta, and terminal run events. The
  expected G1 backend-placeholder error was returned to the model.
- A harmless destructive-command probe emitted `approval.request`. Posting a
  `deny` decision emitted `approval.responded`, prevented execution, completed
  the tool as an error, and allowed the model to produce a final response.
- Hermes 0.18 accepts approval modes `manual`, `smart`, and `off`. The template
  now explicitly uses `manual` instead of relying on fallback from invalid
  legacy wording `ask`.

## Next action

Obtain user approval for G1, then start G2. Before routine sidecar use, generate
`HERMES_API_KEY` with `openssl rand -hex 32`; G1 used a local temporary token
when that value was blank.

## Recovery protocol

1. Read `docs/PROGRESS.md` and `docs/DECISIONS.md`.
2. Run `git status --short --branch` and inspect the last commit.
3. Run the verification command recorded for the active gate.
4. Continue only the active gate; do not start later work with an unverified
   working tree.
