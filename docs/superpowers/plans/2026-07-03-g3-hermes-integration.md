# G3 Hermes Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the persisted FastAPI application to Hermes 0.18 so live model-selected tools, application approvals, and macOS developer-tool controls use the same public API and React UI as Mock mode.

**Architecture:** FastAPI starts a local run and asynchronously mirrors a Hermes `/v1/runs` SSE stream into normalized SQLite events. It passes the local run ID as Hermes `session_id`, allowing the project plugin to call authenticated internal endpoints for order reads and blocking approval proposals. A plugin `pre_tool_call` hook applies workspace path checks and application approval to terminal, write, and patch without changing Hermes core.

**Tech Stack:** FastAPI, SQLite, HTTPX, Hermes project plugin, pytest, macOS `sandbox-exec`.

---

### Task 1: Hermes Client and Event Normalization

**Files:**
- Create: `backend/zc_agent_desk/hermes.py`
- Test: `tests/g3/test_hermes_adapter.py`

- [ ] Write a failing test with `httpx.MockTransport` covering run creation, `session_id`, conversation history, bearer authentication, SSE parsing, approval forwarding, cancellation, and upstream error mapping.
- [ ] Run `.venv/bin/pytest tests/g3/test_hermes_adapter.py -q` and confirm the import fails.
- [ ] Implement `HermesClient.start_run`, `events`, `approve`, and `cancel` with no knowledge of SQLite or FastAPI.
- [ ] Run the focused test and commit as `feat: add hermes sidecar client`.

### Task 2: Live Application Runtime

**Files:**
- Modify: `backend/zc_agent_desk/app.py`
- Test: `tests/g3/test_live_runtime.py`

- [ ] Write failing API tests that create a live run, observe normalized `message.delta`, tool, completion, and failure events, persist the final assistant response, and forward cancellation.
- [ ] Add `mode` and injected Hermes client parameters to `create_app`; keep Mock behavior unchanged.
- [ ] Start Hermes consumption in a FastAPI background task, persist the upstream run ID, normalize public events, and map terminal outcomes to application status.
- [ ] Run all backend tests and commit as `feat: add live hermes runtime adapter`.

### Task 3: Authenticated Business Tool Bridge

**Files:**
- Modify: `.hermes/plugins/zc-agent-desk/__init__.py`
- Modify: `backend/zc_agent_desk/app.py`
- Test: `tests/g3/test_business_bridge.py`
- Test: `tests/g1/test_hermes_plugin_contract.py`

- [ ] Write failing tests for bridge authentication, existing/missing order responses, todo proposal state, approval-before-persistence, rejection, replay, and proposal timeout.
- [ ] Implement plugin HTTP calls using `ZC_AGENT_DESK_BASE_URL`, `HERMES_API_KEY`, and handler `session_id`; never log either credential.
- [ ] Add internal FastAPI endpoints for order reads and blocking todo proposals. Proposal registration emits one `approval.required` event; the handler waits for a persisted approval decision before returning to Hermes.
- [ ] Keep todo insertion in the public approval transaction so the UI sees the side effect immediately and the unique run constraint prevents replay.
- [ ] Run focused and full tests, then commit as `feat: connect hermes business tools`.

### Task 4: Developer Tool Approval and Path Policy

**Files:**
- Create: `.hermes/plugins/zc-agent-desk/policy.py`
- Modify: `.hermes/plugins/zc-agent-desk/__init__.py`
- Create: `scripts/render_hermes_config.py`
- Test: `tests/g3/test_developer_tool_policy.py`

- [ ] Write failing tests for relative workspace paths, absolute outside paths, `..` traversal, existing symlink escape, V4A patch headers, terminal workdir escape, and non-macOS denial.
- [ ] Implement `realpath`-based validation. Require approval for every terminal, write, and patch call; reject unverifiable multi-file patch input before approval.
- [ ] Register a synchronous `pre_tool_call` hook that blocks until the authenticated application proposal is approved, returns a plugin block directive on rejection, and otherwise allows Hermes to execute.
- [ ] Generate runtime config from the tracked template: macOS keeps terminal/file toolsets and other systems omit them. No secret value enters generated or tracked YAML.
- [ ] Run security and plugin tests, then commit as `feat: enforce hermes developer tool policy`.

### Task 5: Live Verification and Gate Record

**Files:**
- Modify: `scripts/dev.sh`
- Modify: `README.md`
- Modify: `docs/PROGRESS.md`
- Modify: `docs/DECISIONS.md`
- Modify: `docs/AI_COLLABORATION.md`

- [ ] Start FastAPI in Hermes mode, render the isolated Hermes config, and start the pinned sidecar under the macOS sandbox.
- [ ] In the React UI verify ordinary text, history, `ORD-1001`, todo approval, todo rejection, terminal approval denial, and refresh recovery.
- [ ] Run backend, frontend, production build, source-lock check, secret scan, and `git diff --check`.
- [ ] Record exact evidence and limitations, commit as `docs: complete g3 hermes integration`, and stop at the G4 approval gate.
