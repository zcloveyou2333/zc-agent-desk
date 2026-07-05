from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/runtime_mode.sh"


def resolve(tmp_path: Path, mode: str, *, configured: bool = False) -> subprocess.CompletedProcess[str]:
    executable = tmp_path / ".vendor/hermes-venv/bin/hermes"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)
    env = {"PATH": os.environ["PATH"]}
    if configured:
        env.update(
            OPENAI_API_KEY="provider-secret",
            OPENAI_BASE_URL="https://provider.invalid/v1",
            MODEL_NAME="test-model",
            HERMES_API_KEY="bridge-secret",
        )
    command = (
        f"source {SCRIPT}; "
        f"resolve_runtime_mode {tmp_path} {mode} || exit $?; "
        "printf '%s %s' \"$APP_MODE\" \"$HERMES_ENABLED\""
    )
    return subprocess.run(["zsh", "-c", command], text=True, capture_output=True, env=env)


def test_auto_enables_only_workflow_without_configuration(tmp_path) -> None:
    result = resolve(tmp_path, "auto")

    assert result.returncode == 0
    assert result.stdout == "auto 0"


def test_auto_enables_hermes_when_environment_is_complete(tmp_path) -> None:
    result = resolve(tmp_path, "auto", configured=True)

    assert result.returncode == 0
    assert result.stdout == "auto 1"


def test_mock_never_enables_hermes(tmp_path) -> None:
    result = resolve(tmp_path, "mock", configured=True)

    assert result.returncode == 0
    assert result.stdout == "mock 0"


def test_hermes_fails_without_exposing_values_when_configuration_is_missing(tmp_path) -> None:
    result = resolve(tmp_path, "hermes")

    assert result.returncode != 0
    assert "Hermes mode requires" in result.stderr
    assert "provider-secret" not in result.stderr
    assert "bridge-secret" not in result.stderr
