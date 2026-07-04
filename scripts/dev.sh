#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Backend environment missing. Run: .venv/bin/python -m pip install -e '.[dev]'" >&2
  exit 1
fi
if [[ ! -d frontend/node_modules ]]; then
  echo "Frontend dependencies missing. Run: cd frontend && npm install" >&2
  exit 1
fi

cleanup() {
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

PYTHONPATH=backend .venv/bin/uvicorn zc_agent_desk.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
npm --prefix frontend run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!

echo "ZC Agent Desk: http://127.0.0.1:5173"
wait
