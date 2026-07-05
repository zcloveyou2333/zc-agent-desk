# Inline Run Trace Design

## Goal

Make agent execution visible inside the conversation, following the compact
Manus-style pattern selected by the user, while preserving the right-hand
Agent Trace as the complete audit view. Tool progress and failures must become
understandable without exposing credentials, provider payloads, stack traces,
or private local paths.

## Selected interaction

Each user turn that creates a run owns one inline execution card positioned
between the user message and the final assistant reply. The card is compact by
default and expandable:

- Running: `正在调用 查询业务订单…`
- Completed: `已完成 1 个工具调用 · 0.01 秒`
- Failed: a friendly summary such as `模型请求失败`
- Awaiting approval: the existing approval controls remain visible inside the
  same turn group.

Expanded content lists ordered tool steps with display names, sanitized
arguments, result summaries, durations, and sanitized technical failure data.
The card does not reproduce token-delta events because those are generation
transport details rather than user-meaningful actions.

## Data model and API

Messages gain a nullable `run_id`. The user message inserted by `create_run`
and the final assistant message produced by that run carry the same run ID.
This explicit relationship is required to place cards correctly; timestamp
inference is rejected because concurrent or retried runs would be ambiguous.

SQLite initialization performs an additive migration for existing databases.
Historical messages without `run_id` continue to render normally. The
conversation detail API includes `run_id` on messages and already includes
runs with ordered events, so no new public endpoint is required.

## Frontend structure

A focused `RunActivityCard` component converts one run's events into a view
model. `ChatWorkspace` groups messages by `run_id`, renders the user message,
then its activity card and approval UI, then the assistant response. Unlinked
historical messages remain in chronological order.

`App` merges each incoming SSE event into the active conversation detail using
the `(run_id, sequence)` identity, then refreshes once after the stream ends.
This provides immediate tool-state changes without polling and preserves the
database as the final source of truth after refresh or reconnection.

The right-hand `Inspector` keeps collapsed token deltas but adds state-specific
styling and details:

- `tool.completed` with `error: true` is a failed tool node.
- `run.failed` is a failed run node.
- Failure nodes show a friendly summary and an expandable sanitized detail.

## Event presentation

Tool display names are mapped in the frontend:

- `query_mock_business` -> `查询业务订单`
- `create_todo` -> `创建待办`
- `terminal` -> `执行终端命令`
- file write/patch tools -> `修改文件`

Unknown tools fall back to their protocol name. Arguments are rendered from
the normalized application event only. Long values are truncated. Keys whose
names contain `key`, `token`, `secret`, `authorization`, or `password` are
replaced with `[已隐藏]`. Result summaries use normalized fields and never raw
provider responses.

## Failure behavior

The application currently receives final Hermes failures but not its internal
retry log stream. This release therefore shows final `run.failed` and failed
`tool.completed` events accurately; it does not invent retry progress. If the
sidecar protocol later exposes retry events, they can be added without changing
the card boundary.

User-facing summaries are stable and localized. Expandable technical details
may include a sanitized error category and application message. API keys,
provider bodies, traceback text, provider account data, and absolute local
paths are excluded at the backend boundary.

## Accessibility and responsive behavior

The card uses a native button for expansion with `aria-expanded`. Status is
communicated through text and icon as well as color. The card fits the existing
chat width and becomes a single-column detail list on narrow screens.

## Test strategy

- Backend migration: old databases gain nullable `run_id` without data loss.
- Backend correlation: user and assistant messages share the creating run ID.
- View model: running, successful, failed-tool, failed-run, and unknown-tool
  events produce stable summaries and sanitized details.
- Component: cards expand/collapse and failed states are accessible.
- Streaming: meaningful events appear before completion and duplicate replayed
  events are ignored.
- Inspector: failed tool and run events use failure styling and expose the
  sanitized summary.
- Regression: approvals, refresh recovery, Mock mode, Hermes mode, and the
  production build continue to pass.

## Out of scope

- Surfacing Hermes internal retry attempts before its run terminates.
- Persisting or displaying chain-of-thought/reasoning tokens.
- Rendering raw tool/provider payloads.
- Redesigning the conversation rail, composer, or todo inspector.
