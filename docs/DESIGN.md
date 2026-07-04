# ZC Agent Desk Design

## Goal

Deliver an internal employee chatbot that demonstrates multi-turn conversation,
model-selected tools, a real approval boundary for write operations, a zero-key
mock mode, and an optional Hermes-backed runtime.

The product title is **ZC Agent Desk** and the byline is **Built by zcloveyou**.

## Runtime boundaries

- React owns input, rendering, approval controls, and the trace viewer.
- FastAPI owns the public API, conversations, persistence, run state, mock
  behavior, and normalization of runtime events.
- Hermes runs as a sidecar and owns the live model/tool loop.
- A project-local Hermes plugin supplies `query_mock_business` and
  `create_todo` without patching Hermes core.
- SQLite stores conversations, messages, runs, events, approvals, todos, and
  deterministic mock orders.

The Input -> Message -> History -> System -> API -> Tokens -> Tools -> Loop ->
Render -> Hooks -> Await sequence is an explanatory lifecycle and trace model,
not an eleven-directory source layout.

## Modes

`APP_MODE=mock` needs no API key or Hermes installation. It must exercise the
same public run, event, tool, and approval contracts as live mode.

`APP_MODE=hermes` sends runs to a pinned Hermes sidecar configured with an
OpenAI-compatible Chat Completions endpoint that supports structured tool
calls. The model identifier is supplied through `MODEL_NAME`, matching the
existing local project convention.

## Tools

- `query_mock_business(order_id)` is read-only and executes automatically.
- `create_todo(title, due_at?, priority?)` pauses before persistence. Approval
  creates exactly one todo; rejection, timeout, or replay creates none.
- Hermes developer tools may expose terminal and file operations on macOS only.
  Commands and mutations require approval. The operating-system policy is a
  local safeguard, not a production-grade cross-platform sandbox.

## Run state

Runs transition through `queued`, `running`, `awaiting_approval`, and one of
`completed`, `failed`, or `cancelled`. Approval, rejection, and cancellation are
idempotent.

Public events are `message.delta`, `tool.started`, `approval.required`,
`tool.completed`, `message.completed`, and `run.failed`. Events have monotonic
sequence numbers so an SSE client can reconnect from its last seen event.

## Deliberate exclusions

The MVP does not include authentication, deployment, retrieval-augmented
generation, multi-user authorization, or complex multi-tool planning.
