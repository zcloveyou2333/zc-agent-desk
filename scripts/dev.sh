#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REQUESTED_MODE="${APP_MODE:-}"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [[ -n "$REQUESTED_MODE" ]]; then
  APP_MODE="$REQUESTED_MODE"
fi
export APP_MODE="${APP_MODE:-mock}"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Backend environment missing. Run: .venv/bin/python -m pip install -e '.[dev]'" >&2
  exit 1
fi
if [[ ! -d frontend/node_modules ]]; then
  echo "Frontend dependencies missing. Run: cd frontend && npm install" >&2
  exit 1
fi

cleanup() {
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" "${HERMES_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

PYTHONPATH=backend .venv/bin/uvicorn zc_agent_desk.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

if [[ "$APP_MODE" == "hermes" ]]; then
  if [[ ! -x .vendor/hermes-venv/bin/hermes ]]; then
    echo "Hermes environment missing. Complete the pinned Hermes setup first." >&2
    exit 1
  fi
  if [[ -z "${HERMES_API_KEY:-}" ]]; then
    echo "HERMES_API_KEY is required for Hermes mode." >&2
    exit 1
  fi
  .venv/bin/python scripts/render_hermes_config.py
  export API_SERVER_KEY="$HERMES_API_KEY"
  export HERMES_HOME="$ROOT/.hermes/runtime"
  export HERMES_ENABLE_PROJECT_PLUGINS=1
  export ZC_AGENT_DESK_BASE_URL="${ZC_AGENT_DESK_BASE_URL:-http://127.0.0.1:8000}"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    /usr/bin/sandbox-exec -f security/macos-hermes.sb \
      -D "WORKSPACE=$ROOT" -D "USER_HOME=$HOME" \
      .vendor/hermes-venv/bin/hermes gateway run &
  else
    .vendor/hermes-venv/bin/hermes gateway run &
  fi
  HERMES_PID=$!
fi

npm --prefix frontend run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!

echo "ZC Agent Desk ($APP_MODE): http://127.0.0.1:5173"
wait
