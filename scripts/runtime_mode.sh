#!/usr/bin/env bash

real_runtime_configured() {
  local root="$1"
  [[ -x "$root/.vendor/hermes-venv/bin/hermes" ]] &&
    [[ -n "${OPENAI_API_KEY:-}" ]] &&
    [[ -n "${OPENAI_BASE_URL:-}" ]] &&
    [[ -n "${MODEL_NAME:-}" ]] &&
    [[ -n "${HERMES_API_KEY:-}" ]]
}

resolve_runtime_mode() {
  local root="$1"
  local requested="${2:-auto}"
  case "$requested" in
    auto)
      APP_MODE=auto
      if real_runtime_configured "$root"; then HERMES_ENABLED=1; else HERMES_ENABLED=0; fi
      ;;
    mock)
      APP_MODE=mock
      HERMES_ENABLED=0
      ;;
    hermes)
      if ! real_runtime_configured "$root"; then
        echo "Hermes mode requires its installed environment and all required variables." >&2
        return 1
      fi
      APP_MODE=hermes
      HERMES_ENABLED=1
      ;;
    *)
      echo "APP_MODE must be auto, mock, or hermes." >&2
      return 1
      ;;
  esac
  export APP_MODE HERMES_ENABLED
}
