# Progress and Recovery

## Current gate

G5 - Public repository published; inline run trace feature is under review on a
dedicated branch.

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
- FastAPI and SQLite persist conversations, messages, runs, ordered events,
  approvals, todos, and mock orders.
- The deterministic Mock Runtime supports ordinary context, existing and
  missing orders, todo approval/rejection, idempotent replay, cancellation, and
  SSE replay from `Last-Event-ID`.
- The selected React enterprise-console UI renders three desktop columns,
  inline approvals, Trace, and todos, then stacks responsively below 900px.
- FastAPI starts Hermes runs asynchronously, mirrors normalized SSE events into
  SQLite, persists final responses, and forwards cancellation.
- The authenticated project plugin reads mock orders and blocks todo,
  terminal, write, and patch calls on application approval without modifying
  Hermes core.
- Hermes is pinned to upstream commit `5445e42b`, and the clean installer
  verifies critical hashes before creating its isolated environment.
- Public documentation now covers architecture, AI decisions, startup,
  limitations, release checks, and the 8–12 minute recording plan.
- Git history uses the approved public author identity, and `main` is published
  at `zcloveyou2333/zc-agent-desk` without local secrets or runtime data.

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

## G2 evidence

- Backend G1+G2 suite: 18 tests passed before final combined verification.
- Frontend API, component, StrictMode regression, and SSE replay suite: 7 tests
  passed; the Vite production build completed.
- Real browser acceptance verified `ORD-1001`, an approval-gated todo, exactly
  one persisted todo, full Trace, refresh restoration, and a 760px viewport.
- A StrictMode probe exposed duplicate first-conversation creation. A regression
  test now wraps the app in StrictMode and the initialization guard prevents it.

## G3 evidence

- Real Hermes UI order query autonomously called `query_mock_business` and
  returned `ORD-1001` as shipped.
- Real `create_todo` paused in the UI, persisted exactly once after approval,
  returned its result to Hermes, and produced a final assistant response.
- Real `terminal pwd` paused with command-specific UI; rejection prevented
  execution and the final response reported the rejected tool result.
- Browser acceptance found and fixed live-mode labeling, delta Trace flooding,
  approval-card refresh deadlock, generic approval wording, and a late-proposal
  cancellation race.
- The relay produced intermittent request timeouts during live validation;
  retries eventually completed. This is recorded as an upstream limitation.

## G4 evidence

- A real local `git clone` with no `.env`, `.vendor`, virtual environment, or
  Node modules installed successfully from README instructions.
- That clone passed 39 backend tests, 8 frontend tests, the Vite production
  build, a 63-file release scan, and actual Mock API/UI startup.
- The first clean install exposed ambiguous setuptools package discovery. A
  failing regression test now fixes discovery to `backend/zc_agent_desk`.
- A second clean clone downloaded immutable Hermes commit `5445e42b`, verified
  all three locked hashes, installed Hermes 0.18.0, and reported the expected
  upstream revision.
- The release scan rejects macOS user paths, key-shaped secrets, missing
  delivery documents, and a mutable Hermes source reference.

## Next action

Review and merge `codex/inline-run-trace` after verification. Then record the
8–12 minute demo and perform the final video privacy review before sending the
repository and video links to HR.

## Inline run trace evidence

- An additive migration links new user and assistant messages to their run;
  historical messages remain valid with a null link.
- Conversation cards show running, completed, approval, failed-tool, and
  failed-run states with expandable sanitized arguments and results.
- Incoming SSE events merge by `(run_id, sequence)` before final refresh, so
  tool activity appears while the run is still active without duplicate replay.
- Agent Trace marks failed tools and runs in red and exposes a sanitized failure
  detail disclosure. Hermes internal retry logs remain intentionally out of
  scope until they are part of the sidecar event protocol.
- Real Mock browser acceptance verified order lookup, expansion, refresh
  recovery, and a 760px responsive viewport.

## Recovery protocol

1. Read `docs/PROGRESS.md` and `docs/DECISIONS.md`.
2. Run `git status --short --branch` and inspect the last commit.
3. Run the verification command recorded for the active gate.
4. Continue only the active gate; do not start later work with an unverified
   working tree.
