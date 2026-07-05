# Workflow Runtime and Keyword Analysis Design

## Goal

Let users switch between a zero-key deterministic Workflow runtime and the
Hermes-backed Real Agent without restarting the application. Introduce one
formal multi-step workflow, named `关键词分析`, that preserves the useful
classification and aggregation logic from the private decision-support project
while using only synthetic public data.

## Product language and assignment compatibility

The UI exposes two choices:

- **Workflow** — pre-orchestrated business flows triggered by natural language,
  with no API key.
- **Real Agent** — Hermes and a real model select and execute tools.

Workflow is the project's implementation of the assignment's required Mock
mode. README and architecture documentation state this explicitly. Existing
`APP_MODE=mock` remains a supported compatibility/diagnostic setting; public
run requests use `workflow` and `hermes`, while the backend accepts `mock` as an
alias for `workflow` during migration.

The selected runtime affects only new messages. One conversation may contain
runs from both runtimes. Existing messages and results never change when the
selection changes.

## Runtime availability and startup

`APP_MODE` gains three operational values:

- `auto` (recommended): always enables Workflow; enables and starts Hermes only
  when the pinned environment and required variables are present.
- `mock`: enables Workflow only and never starts Hermes.
- `hermes`: requires Hermes configuration and fails fast when unavailable.

FastAPI owns two runtime capabilities rather than one global run behavior. The
health response reports each runtime independently:

```json
{
  "status": "ok",
  "mode": "auto",
  "runtimes": {
    "workflow": {"available": true},
    "hermes": {"available": false, "reason": "Real Agent 尚未配置"}
  }
}
```

Reasons are stable, localized, and contain no provider URL, model name, path,
or credential information. A Real Agent request when unavailable returns HTTP
503 and never silently falls back to Workflow.

`scripts/dev.sh` evaluates availability without printing secret values. Under
`auto`, it starts the Hermes sidecar only when its executable and the four
required variables are present. Frontend and FastAPI always start.

## Run API and persistence

`POST /api/conversations/{id}/runs` accepts:

```json
{"message": "分析 2026-06 飘窗垫的关键词需求", "mode": "workflow"}
```

Runs gain a non-null `runtime_mode` column. SQLite initialization adds the
column to existing databases and backfills historical runs as `workflow` when
the old process mode was Mock and `hermes` when it was Hermes. New API responses
include the stored mode. The inline activity card displays the mode so mixed
conversation history remains understandable.

The frontend stores the selected runtime in local storage. On load, it validates
the preference against health capabilities and falls back to Workflow when Real
Agent is unavailable. A segmented control near the composer changes only future
runs. The left runtime badge describes server capability rather than pretending
the whole process is in one runtime.

## Workflow boundary

The project adds a small internal workflow package with three responsibilities:

- `WorkflowRegistry`: register definitions and select one from natural language.
- `WorkflowDefinition`: name, trigger, parameter extraction, ordered steps, and
  final rendering contract.
- `KeywordAnalysisWorkflow`: the only registered definition in this release.

This is deliberately not a generic agent framework. It does not copy
AgentScope, `BaseSkill`, LLM planners, validators, or report agents from the
reference repository. The reusable idea is a named skill with explicit inputs,
steps, dependencies, structured intermediate results, and observable status.

Existing order and todo routes remain as lightweight deterministic tool demos.
They are not presented as additional formal workflows in this release.

## Keyword Analysis workflow

The public name is exactly `关键词分析`.

### Trigger and parameters

The workflow matches natural-language requests containing combinations such as
`关键词分析`, `关键词需求`, or `分析…关键词`. It extracts:

- `year_month`: `YYYY-MM`, `YYYY年M月`, or `M月` (using the current year).
- `category_name`: the supported synthetic category mentioned in the request.

This release seeds at least `飘窗垫` and `办公背包` so the route is demonstrable
without proprietary data. If the workflow is recognized but required parameters
are missing, it completes with a clarification message and parameter-extraction
events; it is not marked as infrastructure failure.

### Ordered steps

1. `识别关键词分析 Workflow`
2. `提取月份与类目`
3. `查询合成关键词数据`
4. `分类八大需求`
5. `计算趋势与高增长词根`
6. `生成分析结果`

Each step emits normalized `tool.started` and `tool.completed` events with a
stable machine tool name, Chinese display label, duration, error flag, and a
small structured result summary. Full synthetic rows remain server-side or are
truncated before entering event payloads.

### Synthetic dataset and analysis

The tracked dataset contains invented keyword rows across the eight requirement
types:

- 品类需求
- 属性需求
- 人群需求
- 风格需求
- 场景需求
- 功能需求
- 品牌需求
- 定制需求

Each row includes category, month, requirement type, word root, search
popularity, month-over-month growth, and source requirement share. Analysis:

- group by requirement type;
- sort each group by search popularity and keep Top 20;
- sum search popularity per requirement;
- calculate each requirement's share against the eight-type total;
- identify high-growth roots where popularity is at least 10,000 and growth is
  at least 15%;
- produce deterministic conclusions and action suggestions from the highest
  share, highest popularity, and highest growth groups.

No LLM is used for routing, validation, or report generation. The result is a
concise readable response; expanded activity details expose normalized counts
and summaries rather than an enormous raw table.

## Existing deterministic behavior

Workflow mode continues to support ordinary context recall, mock order lookup,
and approval-gated todo creation so all original assignment acceptance paths
remain valid. Keyword Analysis is an additional formal workflow selected before
the existing intent handlers.

## Error and security behavior

- Unsupported synthetic category: complete with supported demo categories.
- Missing month/category: complete with a precise clarification request.
- Invalid month: complete with accepted formats.
- Malformed synthetic row or step exception: emit failed tool and `run.failed`
  with a stable sanitized message.
- Real Agent unavailable: HTTP 503 before a run or message is persisted.
- Real provider failures: retain current sanitized Hermes failure handling.
- Never copy the private data-platform endpoint, authorization logic, prompts,
  production values, or real business records.

## Test strategy

- Registry selects Keyword Analysis and does not misclassify ordinary chat.
- Parameter extraction covers ISO and Chinese month formats plus missing data.
- Dataset is synthetic, contains all eight requirement types, and has no private
  source strings.
- Analysis verifies Top 20 ordering, shares sum to approximately 100%, and
  high-growth filtering.
- Workflow emits ordered step events and a deterministic final response.
- Existing order, todo, context, approval, replay, and zero-key tests remain.
- Per-run runtime selection supports mixed history and persists `runtime_mode`.
- Unavailable Hermes returns 503 without persistence.
- Health capability response and `auto`/`mock`/`hermes` startup contracts.
- Frontend toggle persistence, disabled Real state, request mode, and mixed-run
  labels.
- Full backend/frontend tests, production build, release scan, shell syntax,
  and real-browser switching acceptance.

## Out of scope

- Additional formal workflows beyond Keyword Analysis.
- Real data-platform access or user-provided dataset upload.
- LLM-generated Workflow reports, validation agents, or planning.
- A generic DAG editor, parallel workflow steps, or workflow authoring UI.
- Automatically switching a failed Real Agent run to Workflow.
