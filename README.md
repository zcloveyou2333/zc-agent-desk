# ZC Agent Desk

> Built by zcloveyou

ZC Agent Desk is an internal employee chatbot MVP built to demonstrate
multi-turn conversation, model-selected tools, explicit approval for write
operations, deterministic zero-key operation, and an optional Hermes-backed
agent runtime.

## What this MVP proves

The assignment asks for a locally runnable employee chatbot, not a production
platform. This release therefore concentrates on one complete vertical slice:
persisted multi-turn chat, agent-selected business tools, approval before a
write effect, event Trace, failure handling, and zero-key evaluation. Login,
deployment, RAG, multi-user authorization, and complex orchestration are
deliberately excluded.

## Runtime modes

- `mock`: offline, deterministic, and suitable for evaluation without API keys.
- `hermes`: live OpenAI-compatible Chat Completions through a pinned Hermes
  sidecar. The same FastAPI API, SQLite state, approval cards, and Trace UI are
  used in both modes.

## Quick start: Mock mode

Requirements: Python 3.11 or newer and Node.js 20 or newer. Mock mode does not
read `OPENAI_API_KEY`, does not start Hermes, and does not require `.env`.

```bash
git clone <repository-url> zc-agent-desk
cd zc-agent-desk
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix frontend ci
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

Hermes mode additionally requires Git and the pinned Hermes source. The setup
script checks out immutable commit `5445e42b`, verifies compatibility-critical
file hashes, and installs it under ignored `.vendor/` directories.

```bash
./scripts/setup_hermes.sh
cp .env.example .env
# Edit .env, then generate HERMES_API_KEY with: openssl rand -hex 32
APP_MODE=hermes ./scripts/dev.sh
```

Set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `MODEL_NAME` for an
OpenAI-compatible Chat Completions endpoint that supports structured
`tool_calls`. `HERMES_API_KEY` is a random local bridge secret shared only by
FastAPI and the loopback Hermes sidecar; it is not a provider key. Never paste
these values into source files or commit `.env`.

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
cd ..
./scripts/setup_hermes.sh --verify-only  # after Hermes installation
.venv/bin/python scripts/release_check.py
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

The frontend sends a run request, reconnectable SSE carries normalized events,
and SQLite is the source of truth for refresh recovery. In Mock mode an
explicit deterministic router selects tools. In Hermes mode the model selects
tools; the plugin calls an authenticated FastAPI bridge and blocks write or
developer actions until approval. Tool results return to the runtime before the
final assistant response.

See [architecture](docs/ARCHITECTURE.md), [design](docs/DESIGN.md),
[decisions](docs/DECISIONS.md), [AI collaboration](docs/AI_COLLABORATION.md),
and the [recording checklist](docs/RECORDING.md).

## Current limitations

- Mock intent routing is intentionally deterministic rather than pretending to
  be a language model.
- Authentication, deployment, RAG, and multi-user permissions are out of scope.
- The third-party relay can be slow or time out; the app records a sanitized
  run failure and never exposes provider diagnostics or credentials.
- The macOS policy is a local MVP safeguard, not a production security sandbox.
- Hermes mode depends on a compatible OpenAI-style relay; Mock mode remains the
  portable evaluation path on every supported platform.

## Security

Never commit `.env`, API keys, tokens, private account data, or unredacted
recordings. Local macOS command confinement is an MVP safeguard and is not
presented as a production-grade sandbox.
