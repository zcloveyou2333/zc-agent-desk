# ZC Agent Desk

> Built by zcloveyou

ZC Agent Desk is an internal employee chatbot MVP built to demonstrate
multi-turn conversation, model-selected tools, explicit approval for write
operations, deterministic zero-key operation, and an optional Hermes-backed
agent runtime.

## Current status

G2 provides a runnable zero-key Mock vertical slice: persisted conversations,
ordinary multi-turn replies, mock order lookup, todo approval, SSE event replay,
Agent Trace, and a responsive React workspace. Live Hermes integration remains
behind the G3 approval gate.

## Runtime modes

- `mock`: offline, deterministic, and suitable for evaluation without API keys.
- `hermes`: live OpenAI-compatible Chat Completions through a pinned Hermes
  sidecar. G1 feasibility is verified; product integration is scheduled for G3.

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
- Hermes developer tools and the FastAPI-to-Hermes adapter belong to G3.

## Security

Never commit `.env`, API keys, tokens, private account data, or unredacted
recordings. Local macOS command confinement is an MVP safeguard and is not
presented as a production-grade sandbox.
