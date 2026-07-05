# Workflow Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the zero-key `关键词分析` Workflow and Hermes Real Agent from one application, with a per-message UI switch and no service restart.

**Architecture:** Add per-run runtime selection and capability reporting to FastAPI, then implement a small deterministic workflow registry with one synthetic-data keyword analysis workflow. `dev.sh` chooses safe startup capabilities, while React persists the user's selection and sends it with each new run.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest, Bash, React 19, TypeScript, Vitest, Testing Library.

---

## File map

- Create `backend/zc_agent_desk/workflows/base.py`: workflow contracts and registry.
- Create `backend/zc_agent_desk/workflows/keyword_analysis.py`: extraction, analysis, steps, rendering.
- Create `backend/zc_agent_desk/workflows/synthetic_keywords.json`: invented public fixtures.
- Create `backend/zc_agent_desk/workflows/__init__.py`: default registry construction.
- Modify `pyproject.toml`: package the tracked synthetic JSON fixture.
- Create `tests/workflows/test_keyword_analysis.py`: deterministic unit coverage.
- Create `tests/g5/test_runtime_selection.py`: API migration, mixed runtime, availability.
- Modify `backend/zc_agent_desk/app.py`: per-run mode, capability health, workflow execution.
- Modify `scripts/dev.sh`: `auto` detection and optional Hermes startup.
- Create `scripts/runtime_mode.sh`: testable startup capability resolution.
- Modify `.env.example`: recommended `APP_MODE=auto`.
- Modify `tests/g1/test_environment_contract.py`: startup contract checks.
- Modify `frontend/src/types.ts`: runtime capability and run mode types.
- Modify `frontend/src/api.ts` and `api.test.ts`: submit selected mode.
- Create `frontend/src/components/RuntimeSwitch.tsx` and test: accessible segmented control.
- Modify `frontend/src/App.tsx`, `App.test.tsx`, `ChatWorkspace.tsx`, `ConversationRail.tsx`, and `styles.css`: selection persistence, disabled Real state, labels.
- Modify `frontend/src/runActivity.ts`: keyword workflow display labels and runtime label.
- Modify `README.md`, `docs/ARCHITECTURE.md`, `docs/AI_COLLABORATION.md`, and `docs/PROGRESS.md`.

### Task 1: Implement the deterministic Keyword Analysis core

**Files:**
- Create: `backend/zc_agent_desk/workflows/base.py`
- Create: `backend/zc_agent_desk/workflows/keyword_analysis.py`
- Create: `backend/zc_agent_desk/workflows/synthetic_keywords.json`
- Create: `backend/zc_agent_desk/workflows/__init__.py`
- Modify: `pyproject.toml`
- Create: `tests/workflows/test_keyword_analysis.py`

- [ ] **Step 1: Write failing extraction and registry tests**

Define tests for `2026-06`, `2026年6月`, current-year `6月`, missing month,
supported category selection, and ordinary chat not matching:

```python
registry = default_registry()
workflow = registry.match("分析 2026年6月飘窗垫的关键词需求")
assert workflow.name == "关键词分析"
assert workflow.extract_parameters("分析 2026年6月飘窗垫的关键词需求") == {
    "year_month": "2026-06",
    "category_name": "飘窗垫",
}
assert registry.match("你好") is None
```

- [ ] **Step 2: Write failing analysis tests**

Load the fixture and assert all eight requirement types exist, each output list
is sorted descending and at most 20 rows, calculated shares sum to `100 ± 0.1`,
and high-growth roots satisfy popularity `>= 10000` and growth `>= 15`.

- [ ] **Step 3: Run tests and verify RED**

```bash
.venv/bin/pytest -q tests/workflows/test_keyword_analysis.py
```

Expected: import failure because the workflow package does not exist.

- [ ] **Step 4: Implement contracts and fixture**

Define:

```python
@dataclass(frozen=True)
class WorkflowResult:
    content: str
    steps: list[dict[str, Any]]
    clarification: bool = False

class Workflow(Protocol):
    name: str
    def matches(self, message: str) -> bool: ...
    def extract_parameters(self, message: str) -> dict[str, str | None]: ...
    def execute(self, message: str) -> WorkflowResult: ...
```

`WorkflowRegistry.match()` returns the first matching definition. Seed invented
rows for `飘窗垫` and `办公背包` across all eight types; no row may contain a
real endpoint, shop, account, token, or private identifier.

Add the fixture to the editable/wheel package contract:

```toml
[tool.setuptools.package-data]
zc_agent_desk = ["workflows/*.json"]
```

- [ ] **Step 5: Implement keyword analysis**

Extract supported month forms and category names deterministically. Group,
sort, limit, calculate shares, filter high-growth roots, and render concise
Chinese conclusions/action suggestions. Return six ordered step records with
machine names and small result summaries.

- [ ] **Step 6: Run workflow tests and commit**

```bash
.venv/bin/pytest -q tests/workflows/test_keyword_analysis.py
git add backend/zc_agent_desk/workflows tests/workflows/test_keyword_analysis.py pyproject.toml
git commit -m "feat: add keyword analysis workflow"
```

Expected: all workflow tests pass.

### Task 2: Add per-run runtime persistence and API selection

**Files:**
- Modify: `backend/zc_agent_desk/app.py`
- Create: `tests/g5/test_runtime_selection.py`
- Modify: `tests/g2/test_mock_api.py`
- Modify: `tests/g3/test_live_runtime.py`

- [ ] **Step 1: Write failing migration and API tests**

Create a legacy runs table, initialize it, and assert `runtime_mode` exists.
Add mixed-run tests:

```python
workflow_run = client.post(path, json={"message": "你好", "mode": "workflow"})
real_run = client.post(path, json={"message": "hello", "mode": "hermes"})
detail = client.get(conversation_path).json()
assert [run["runtime_mode"] for run in detail["runs"][-2:]] == ["workflow", "hermes"]
```

Assert unavailable Hermes returns 503 before message/run counts change, and
`mode: mock` is stored as `workflow`.

- [ ] **Step 2: Run tests and verify RED**

```bash
.venv/bin/pytest -q tests/g5/test_runtime_selection.py
```

Expected: run schema and request model do not support runtime selection.

- [ ] **Step 3: Implement persistence and capability config**

Add `runtime_mode TEXT NOT NULL DEFAULT 'workflow'` with an additive migration.
Change `RunCreate` to accept `mode: Literal['workflow', 'mock', 'hermes'] =
'workflow'`. `create_app` receives `workflow_enabled` and `hermes_enabled`
booleans derived from operational mode; `create_run` normalizes `mock` to
`workflow`, checks availability before persistence, and dispatches per run.

- [ ] **Step 4: Emit Workflow events**

When the registry matches Keyword Analysis, convert every returned step to
`tool.started` and `tool.completed`, then persist its deterministic final
assistant message. Missing parameters complete with a clarification. Existing
order/todo/context handlers remain the fallback Workflow runtime.

- [ ] **Step 5: Add capability health**

Return `mode` plus `runtimes.workflow` and `runtimes.hermes` availability. Use
only stable reason text `Real Agent 尚未配置`.

- [ ] **Step 6: Run backend suites and commit**

```bash
.venv/bin/pytest -q tests/g5/test_runtime_selection.py tests/g2/test_mock_api.py tests/g3/test_live_runtime.py
.venv/bin/pytest -q
git add backend/zc_agent_desk/app.py tests/g5/test_runtime_selection.py tests/g2/test_mock_api.py tests/g3/test_live_runtime.py
git commit -m "feat: select runtime per message"
```

Expected: all backend tests pass.

### Task 3: Make one startup support Workflow and Real Agent

**Files:**
- Modify: `scripts/dev.sh`
- Modify: `.env.example`
- Modify: `tests/g1/test_environment_contract.py`
- Create: `tests/g5/test_dev_mode_contract.py`

- [ ] **Step 1: Write failing shell-contract tests**

Run `dev.sh` with a temporary project fixture or extract a sourced
`resolve_runtime_mode` function. Verify:

- `auto` with missing credentials resolves to Workflow-only;
- `auto` with all required variables and Hermes executable enables both;
- `mock` never starts Hermes;
- `hermes` with missing requirements exits non-zero with no secret output.

- [ ] **Step 2: Run tests and verify RED**

```bash
.venv/bin/pytest -q tests/g5/test_dev_mode_contract.py tests/g1/test_environment_contract.py
```

Expected: `auto` is unsupported.

- [ ] **Step 3: Implement safe mode resolution**

Move pure mode checks into `scripts/runtime_mode.sh` so tests can source them.
Required Real variables are `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL_NAME`,
and `HERMES_API_KEY`. Export `HERMES_ENABLED=1|0`; start the sidecar only when
enabled. Never print environment values.

- [ ] **Step 4: Update environment defaults and verify**

Set `.env.example` to `APP_MODE=auto`, run:

```bash
.venv/bin/pytest -q tests/g5/test_dev_mode_contract.py tests/g1/test_environment_contract.py
bash -n scripts/dev.sh scripts/runtime_mode.sh
```

Expected: tests pass and shell syntax is valid.

- [ ] **Step 5: Commit startup behavior**

```bash
git add scripts/dev.sh scripts/runtime_mode.sh .env.example tests/g1/test_environment_contract.py tests/g5/test_dev_mode_contract.py
git commit -m "feat: auto-start workflow and real runtimes"
```

### Task 4: Extend the frontend API and runtime types

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/api.test.ts`

- [ ] **Step 1: Write failing API tests**

Assert `createRun('c1', 'hello', 'workflow')` sends
`{"message":"hello","mode":"workflow"}`, and health parses independent
runtime availability/reason data.

- [ ] **Step 2: Run and verify RED**

```bash
npm --prefix frontend test -- --run src/api.test.ts
```

Expected: `createRun` accepts only two arguments and omits mode.

- [ ] **Step 3: Implement types and API**

Add:

```ts
export type RuntimeMode = 'workflow' | 'hermes';
export interface RuntimeCapability { available: boolean; reason?: string }
```

Add `runtime_mode` to `Run`, update `Health`, and send mode in `createRun`.

- [ ] **Step 4: Verify and commit**

```bash
npm --prefix frontend test -- --run src/api.test.ts
npm --prefix frontend run build
git add frontend/src/types.ts frontend/src/api.ts frontend/src/api.test.ts
git commit -m "feat: send runtime with each run"
```

### Task 5: Add the Workflow / Real Agent switch

**Files:**
- Create: `frontend/src/components/RuntimeSwitch.tsx`
- Create: `frontend/src/components/RuntimeSwitch.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/components/ChatWorkspace.tsx`
- Modify: `frontend/src/components/ConversationRail.tsx`
- Modify: `frontend/src/runActivity.ts`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing component tests**

Assert the segmented control exposes two buttons, selected state uses
`aria-pressed`, unavailable Real is disabled with `Real Agent 尚未配置`, and
selecting Real calls `onChange('hermes')`.

- [ ] **Step 2: Write failing App tests**

Mock both runtimes available, select Real, submit, and assert
`createRun('c1', message, 'hermes')`. Remount with stored `hermes` preference and
assert it remains selected. Mock unavailable Real and assert stored preference
falls back to Workflow.

- [ ] **Step 3: Run tests and verify RED**

```bash
npm --prefix frontend test -- --run src/components/RuntimeSwitch.test.tsx src/App.test.tsx
```

Expected: switch is absent and API call lacks runtime.

- [ ] **Step 4: Implement selection and persistence**

Initialize from `localStorage['zc-agent-desk.runtime']`, validate after health
loads, pass selection into `createRun`, and store user changes. Place
`RuntimeSwitch` in the composer. Change the rail badge to `Workflow + Real`
when both are available and `Workflow Runtime` otherwise.

- [ ] **Step 5: Label mixed run history**

Show `Workflow` or `Real Agent` in `RunActivityCard` metadata using each run's
persisted `runtime_mode`. Add labels for the six keyword workflow step names in
`runActivity.ts`.

- [ ] **Step 6: Verify responsive UI and commit**

```bash
npm --prefix frontend test -- --run
npm --prefix frontend run build
git add frontend/src
git commit -m "feat: switch workflow and real agent per message"
```

Expected: all frontend tests and build pass.

### Task 6: Document and release-check the stacked feature

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/AI_COLLABORATION.md`
- Modify: `docs/PROGRESS.md`

- [ ] **Step 1: Update public documentation**

Explain that Workflow is the required Mock implementation, show Keyword
Analysis prompts, document `auto`/`mock`/`hermes`, mixed-mode semantics,
synthetic data, and the explicit non-use of private code/data.

- [ ] **Step 2: Run complete verification**

```bash
.venv/bin/pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run build
bash -n scripts/dev.sh scripts/runtime_mode.sh
.venv/bin/python scripts/release_check.py
git diff --check
```

Expected: zero failures and no secret/privacy findings.

- [ ] **Step 3: Run real-browser acceptance**

Start once in `auto`; verify Workflow Keyword Analysis, Workflow order/todo,
switch to Real Agent without restarting, mixed-mode card labels, unavailable
Real disabled state in a Workflow-only process, refresh persistence, and 760px
layout. Save screenshots only under ignored `output/playwright/`.

- [ ] **Step 4: Commit documentation**

```bash
git add README.md docs/ARCHITECTURE.md docs/AI_COLLABORATION.md docs/PROGRESS.md
git commit -m "docs: explain workflow and real runtimes"
```

- [ ] **Step 5: Review stacked branch scope**

```bash
git status --short --branch
git log --oneline codex/inline-run-trace..HEAD
git diff --stat codex/inline-run-trace...HEAD
```

Expected: clean `codex/workflow-runtime` branch containing only the Workflow
runtime specification, implementation, tests, and documentation. Do not push
or open the stacked PR without user approval.
