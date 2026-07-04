#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$ROOT/config/hermes-source.lock"
SOURCE_DIR="$ROOT/.vendor/hermes-agent"
VENV_DIR="$ROOT/.vendor/hermes-venv"

lock_value() {
  awk -F= -v key="$1" '$1 == key {sub($1 "=", ""); print; exit}' "$LOCK"
}

SOURCE="$(lock_value source)"
COMMIT="$(lock_value commit)"

verify_source() {
  local failed=0
  local name expected path actual
  while read -r name path; do
    expected="$(lock_value "${name}_sha256")"
    actual="$(shasum -a 256 "$SOURCE_DIR/$path" | awk '{print $1}')"
    if [[ "$actual" != "$expected" ]]; then
      echo "Hermes source verification failed: $path" >&2
      failed=1
    fi
  done <<'FILES'
pyproject pyproject.toml
api_server gateway/platforms/api_server.py
plugin_loader hermes_cli/plugins.py
FILES
  return "$failed"
}

if [[ "${1:-}" == "--verify-only" ]]; then
  verify_source
  echo "Hermes source matches pinned commit $COMMIT"
  exit 0
fi

if [[ -e "$SOURCE_DIR" ]]; then
  verify_source
else
  mkdir -p "$ROOT/.vendor"
  git clone --filter=blob:none "$SOURCE" "$SOURCE_DIR"
  git -C "$SOURCE_DIR" checkout --detach "$COMMIT"
  verify_source
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e "$SOURCE_DIR"
echo "Hermes $(lock_value version) is ready in .vendor/hermes-venv"
