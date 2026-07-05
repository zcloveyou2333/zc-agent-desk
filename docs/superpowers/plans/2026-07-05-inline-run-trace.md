# Inline Run Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show each run's tool activity and sanitized failures inline in the conversation while improving failure visibility in Agent Trace.

**Architecture:** Add an additive `messages.run_id` correlation in SQLite and the conversation API. Build a pure frontend event-to-view-model module shared by a new inline activity card and the Inspector, then merge live SSE events into active conversation state by `(run_id, sequence)`.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest, React 19, TypeScript, Vitest, Testing Library, CSS.

---

## File map

- Modify `backend/zc_agent_desk/app.py`: additive migration, message/run correlation, normalized failure details.
- Modify `tests/g2/test_mock_api.py`: migration and Mock correlation coverage.
- Modify `tests/g3/test_live_runtime.py`: Hermes assistant/failure correlation coverage.
- Modify `frontend/src/types.ts`: nullable message `run_id`.
- Create `frontend/src/runActivity.ts`: pure event summarization and sanitization.
- Create `frontend/src/runActivity.test.ts`: view-model unit tests.
- Create `frontend/src/components/RunActivityCard.tsx`: accessible inline disclosure.
- Create `frontend/src/components/RunActivityCard.test.tsx`: component behavior.
- Modify `frontend/src/components/ChatWorkspace.tsx`: render turn groups.
- Modify `frontend/src/components/Inspector.tsx`: failure styling and details.
- Modify `frontend/src/App.tsx`: merge live SSE events.
- Modify `frontend/src/App.test.tsx`: integration and streaming regression tests.
- Modify `frontend/src/styles.css`: inline card and failure presentation.
- Modify `docs/AI_COLLABORATION.md`: record the explicit-correlation decision.

### Task 1: Persist explicit message-to-run correlation

**Files:**
- Modify: `backend/zc_agent_desk/app.py`
- Test: `tests/g2/test_mock_api.py`
- Test: `tests/g3/test_live_runtime.py`

- [ ] **Step 1: Write failing migration and correlation tests**

Add tests that create a legacy `messages` table without `run_id`, call
`Store.initialize()`, and assert `PRAGMA table_info(messages)` contains
`run_id`. Extend the Mock order test to assert:

```python
messages = client.get(f"/api/conversations/{conversation_id}").json()["messages"]
assert messages[-2]["run_id"] == run_id
assert messages[-1]["run_id"] == run_id
```

Extend the live completion test with the same assistant correlation assertion.

- [ ] **Step 2: Run the focused backend tests and verify RED**

Run:

```bash
.venv/bin/pytest -q tests/g2/test_mock_api.py tests/g3/test_live_runtime.py
```

Expected: failures because message responses have no `run_id` and legacy
databases are not migrated.

- [ ] **Step 3: Add the migration and correlation**

After schema creation, inspect `PRAGMA table_info(messages)` and execute:

```python
if "run_id" not in message_columns:
    db.execute("ALTER TABLE messages ADD COLUMN run_id TEXT REFERENCES runs(id)")
```

Change `add_message` to accept `run_id: str | None = None`, insert that column,
and select it in `messages()`. Create the run before inserting the user message
inside the run endpoint, then pass the run ID for both user and assistant
messages. Historical messages remain `None`.

- [ ] **Step 4: Run focused and full backend tests**

Run:

```bash
.venv/bin/pytest -q tests/g2/test_mock_api.py tests/g3/test_live_runtime.py
.venv/bin/pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the backend contract**

```bash
git add backend/zc_agent_desk/app.py tests/g2/test_mock_api.py tests/g3/test_live_runtime.py
git commit -m "feat: correlate messages with agent runs"
```

### Task 2: Build the run activity view model

**Files:**
- Create: `frontend/src/runActivity.ts`
- Create: `frontend/src/runActivity.test.ts`
- Modify: `frontend/src/types.ts`

- [ ] **Step 1: Write failing view-model tests**

Cover successful query, running tool, `tool.completed` with `error: true`, final
`run.failed`, unknown tool fallback, and secret redaction. The key assertion is:

```ts
expect(summarizeRun(failedRun)).toMatchObject({
  tone: 'failed',
  title: '模型请求失败',
  steps: [{ label: '查询业务订单', state: 'failed' }],
});
expect(formatArguments({ api_token: 'secret', order_id: 'ORD-1001' }))
  .toEqual({ api_token: '[已隐藏]', order_id: 'ORD-1001' });
```

- [ ] **Step 2: Run the unit test and verify RED**

Run:

```bash
npm --prefix frontend test -- --run src/runActivity.test.ts
```

Expected: module import fails because `runActivity.ts` does not exist.

- [ ] **Step 3: Implement pure summarization**

Define `ActivityStep`, `RunActivity`, `toolLabel`, `formatArguments`, and
`summarizeRun`. Only `tool.started`, `tool.completed`, `approval.required`, and
`run.failed` become steps. Pair tool completion with the preceding started tool,
derive duration from normalized event data, truncate string values to 160
characters, and redact keys matching:

```ts
/key|token|secret|authorization|password/i
```

Add `run_id: string | null` to `Message`.

- [ ] **Step 4: Run the view-model suite**

```bash
npm --prefix frontend test -- --run src/runActivity.test.ts
```

Expected: all new tests pass.

- [ ] **Step 5: Commit the presentation model**

```bash
git add frontend/src/types.ts frontend/src/runActivity.ts frontend/src/runActivity.test.ts
git commit -m "feat: summarize agent run activity"
```

### Task 3: Render the accessible inline execution card

**Files:**
- Create: `frontend/src/components/RunActivityCard.tsx`
- Create: `frontend/src/components/RunActivityCard.test.tsx`
- Modify: `frontend/src/components/ChatWorkspace.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing component and placement tests**

Render a completed run and assert the disclosure button is collapsed with
`已完成 1 个工具调用`. Click it and assert `查询业务订单` and sanitized arguments
appear. Render a failed run and assert an alert-visible `模型请求失败`. In
`App.test.tsx`, give both messages `run_id: 'r1'` and assert DOM order is user
message, activity card, assistant message.

- [ ] **Step 2: Run focused frontend tests and verify RED**

```bash
npm --prefix frontend test -- --run src/components/RunActivityCard.test.tsx src/App.test.tsx
```

Expected: card module is missing and no inline summary exists.

- [ ] **Step 3: Implement card and turn grouping**

`RunActivityCard` calls `summarizeRun(run)`, uses a native button with
`aria-expanded`, and renders an ordered step list only when expanded. In
`ChatWorkspace`, map messages in order and render the matching run card after a
user message when `message.run_id` matches a run. Render its approval card in
the same group. Keep unlinked pending runs in the existing fallback area so old
data remains usable.

- [ ] **Step 4: Add selected layout styling**

Add `.run-activity`, `.run-activity-toggle`, `.run-activity.failed`,
`.activity-step`, and narrow-screen rules. Use text/icon plus green, blue,
amber, or red tone; do not communicate state by color alone.

- [ ] **Step 5: Run focused and full frontend tests**

```bash
npm --prefix frontend test -- --run src/components/RunActivityCard.test.tsx src/App.test.tsx
npm --prefix frontend test -- --run
```

Expected: all tests pass.

- [ ] **Step 6: Commit the inline card**

```bash
git add frontend/src/components/RunActivityCard.tsx frontend/src/components/RunActivityCard.test.tsx frontend/src/components/ChatWorkspace.tsx frontend/src/App.test.tsx frontend/src/styles.css
git commit -m "feat: show tool activity inside chat"
```

### Task 4: Merge live events and enhance Agent Trace failures

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/components/Inspector.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing streaming and Inspector tests**

Mock `streamRunEvents` so it emits `tool.started` before resolving. Assert the
inline card updates before the final `getConversation` refresh. Add a failed
tool and `run.failed` event and assert Agent Trace renders `工具执行失败`,
`运行失败`, and a visible friendly failure summary.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
npm --prefix frontend test -- --run src/App.test.tsx
```

Expected: live events are ignored except approval and Inspector lacks failed
state details.

- [ ] **Step 3: Merge SSE events idempotently**

Add a callback that updates `detail.runs`: find `event.run_id`, append only when
no event with the same sequence exists, sort by sequence, and derive transient
run status (`awaiting_approval` for approval; `failed` for run failure). Preserve
the final `loadDetail(activeId)` reconciliation after streaming.

- [ ] **Step 4: Enhance Inspector failure presentation**

Reuse `toolLabel` and failure helpers. Add a `failed` class when a tool
completion has `error: true` or the event type is `run.failed`; render sanitized
`message` below the event label. Keep consecutive message deltas collapsed.

- [ ] **Step 5: Run full frontend validation**

```bash
npm --prefix frontend test -- --run
npm --prefix frontend run build
```

Expected: all tests and the TypeScript/Vite build pass.

- [ ] **Step 6: Commit live activity and failure trace**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/components/Inspector.tsx frontend/src/styles.css
git commit -m "feat: stream failures into agent trace"
```

### Task 5: Document, browser-test, and release the feature branch

**Files:**
- Modify: `docs/AI_COLLABORATION.md`
- Modify: `docs/PROGRESS.md`

- [ ] **Step 1: Record the product decision**

Add an AI collaboration row explaining why explicit `run_id` correlation was
chosen over timestamp inference, and record the limitation that Hermes retry
logs are not yet SSE events.

- [ ] **Step 2: Run complete verification**

```bash
.venv/bin/pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run build
.venv/bin/python scripts/release_check.py
git diff --check
```

Expected: zero failures; the known FastAPI TestClient deprecation warning may
remain.

- [ ] **Step 3: Verify real browser behavior**

Start Mock mode, then verify order lookup shows a running/completed inline card,
expansion reveals the tool step, refresh preserves placement, a failed fixture
or test route renders failure styling, and the 760px viewport remains usable.
Capture one screenshot under ignored `output/playwright/`.

- [ ] **Step 4: Commit documentation**

```bash
git add docs/AI_COLLABORATION.md docs/PROGRESS.md
git commit -m "docs: record inline trace verification"
```

- [ ] **Step 5: Review branch before publication**

```bash
git status --short --branch
git log --oneline main..HEAD
git diff --stat main...HEAD
```

Expected: clean `codex/inline-run-trace` branch with only this feature's
specification, implementation, tests, and documentation. Do not push or merge
without user approval.
