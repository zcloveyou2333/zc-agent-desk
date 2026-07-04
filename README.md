# ZC Agent Desk

> Built by zcloveyou

ZC Agent Desk is an internal employee chatbot MVP built to demonstrate
multi-turn conversation, model-selected tools, explicit approval for write
operations, deterministic zero-key operation, and an optional Hermes-backed
agent runtime.

## Current status

G3 provides a runnable zero-key Mock vertical slice: persisted conversations,
ordinary multi-turn replies, mock order lookup, todo approval, SSE event replay,
Agent Trace, and a responsive React workspace. Hermes mode adds live
model-selected tools through the isolated sidecar and authenticated project
plugin bridge.

## Runtime modes

- `mock`: offline, deterministic, and suitable for evaluation without API keys.
- `hermes`: live OpenAI-compatible Chat Completions through a pinned Hermes
  sidecar. The same FastAPI API, SQLite state, approval cards, and Trace UI are
  used in both modes.

## Quick start: Mock mode

Requirements: Python 3.11 or newer and Node.js 20 or newer. Mock mode does not
read `OPENAI_API_KEY`, does not start Hermes, and does not require `.env`.

```bash
cd /Users/zhangchi/Projects/python/chatbot
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cd frontend
npm install
cd ..
./scripts/dev.sh
```

Open <http://127.0.0.1:5173>. The backend listens on
<http://127.0.0.1:8000>; Vite proxies `/api` requests to it.

Useful demo prompts:

- `你好，我叫小雁`, followed by `我刚才说我叫什么？`
- `查询订单 ORD-1001`
- `查询订单 ORD-9999`
- `创建待办：周五提交周报`, then approve or reject the inline card

SQLite data is stored at `data/zc-agent-desk.sqlite3` and survives refreshes.
Delete that ignored file only when you intentionally want a fresh demo.

## Start Hermes mode

Hermes mode additionally requires the verified Hermes 0.18 source and virtual
environment under ignored `.vendor/hermes-agent` and `.vendor/hermes-venv`.
Copy `.env.example` to `.env` and set `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`MODEL_NAME`, and a random `HERMES_API_KEY`. Never paste these values into
source files or commit `.env`.

```bash
APP_MODE=hermes ./scripts/dev.sh
```

The script renders a secret-free isolated config into `.hermes/runtime`, starts
FastAPI, starts Hermes, and starts React. On macOS, Hermes runs under the tracked
`sandbox-exec` policy. On other systems, terminal/file toolsets are omitted by
the config renderer while the two business tools remain available.

Hermes demo prompts:

- `请查询订单 ORD-1001，并告诉我状态`
- `请直接使用 create_todo 工具创建待办：检查G3审批。不要调用其他工具。`
- `请只使用 terminal 工具执行 pwd，不要使用其他工具。`

The second and third prompts pause on an inline approval card. Todo approval
persists exactly once before Hermes receives the result. Developer-tool
approval is handled by the project plugin for every invocation; Hermes' native
dangerous-command approval mode is disabled to avoid double prompts.

## Verification

```bash
.venv/bin/pytest -q
cd frontend
npm test -- --run
npm run build
```

The public application API currently includes:

- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{id}`
- `POST /api/conversations/{id}/runs`
- `GET /api/runs/{run_id}/events`
- `POST /api/runs/{run_id}/approval`
- `POST /api/runs/{run_id}/cancel`
- `GET /api/todos`

See [the design](docs/DESIGN.md), [decisions](docs/DECISIONS.md), and
[implementation plan](docs/IMPLEMENTATION_PLAN.md).

## Current limitations

- Mock intent routing is intentionally deterministic rather than pretending to
  be a language model.
- Authentication, deployment, RAG, and multi-user permissions are out of scope.
- The third-party relay can be slow or time out; the app records a sanitized
  run failure and never exposes provider diagnostics or credentials.
- The macOS policy is a local MVP safeguard, not a production security sandbox.

## Security

Never commit `.env`, API keys, tokens, private account data, or unredacted
recordings. Local macOS command confinement is an MVP safeguard and is not
presented as a production-grade sandbox.
