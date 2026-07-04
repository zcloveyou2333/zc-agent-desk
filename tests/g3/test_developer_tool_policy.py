from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / ".hermes/plugins/zc-agent-desk/policy.py"


def load_policy():
    spec = importlib.util.spec_from_file_location("zc_policy", POLICY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_and_terminal_paths_must_stay_inside_real_workspace(tmp_path) -> None:
    policy = load_policy()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "escape").symlink_to(outside, target_is_directory=True)

    assert policy.validate_tool_call("write_file", {"path": "notes/a.md"}, workspace, "Darwin") is None
    assert "outside workspace" in policy.validate_tool_call(
        "write_file", {"path": str(outside / "x.md")}, workspace, "Darwin"
    )
    assert "outside workspace" in policy.validate_tool_call(
        "write_file", {"path": "../outside/x.md"}, workspace, "Darwin"
    )
    assert "outside workspace" in policy.validate_tool_call(
        "write_file", {"path": "escape/x.md"}, workspace, "Darwin"
    )
    assert "outside workspace" in policy.validate_tool_call(
        "terminal", {"command": "pwd", "workdir": str(outside)}, workspace, "Darwin"
    )


def test_patch_mode_validates_every_declared_path(tmp_path) -> None:
    policy = load_policy()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    safe = "*** Begin Patch\n*** Add File: docs/a.md\n+hello\n*** End Patch"
    escaped = "*** Begin Patch\n*** Update File: ../outside.md\n-old\n+new\n*** End Patch"

    assert policy.validate_tool_call("patch", {"mode": "patch", "patch": safe}, workspace, "Darwin") is None
    assert "outside workspace" in policy.validate_tool_call(
        "patch", {"mode": "patch", "patch": escaped}, workspace, "Darwin"
    )
    assert "cannot verify" in policy.validate_tool_call(
        "patch", {"mode": "patch", "patch": "no file headers"}, workspace, "Darwin"
    )


def test_developer_tools_are_denied_off_macos(tmp_path) -> None:
    policy = load_policy()
    for tool in ("terminal", "write_file", "patch"):
        assert "macOS" in policy.validate_tool_call(tool, {}, tmp_path, "Linux")


def test_config_renderer_omits_developer_tools_off_macos(tmp_path) -> None:
    output = tmp_path / "config.yaml"
    env = os.environ | {
        "MODEL_NAME": "test-model",
        "OPENAI_BASE_URL": "https://relay.example/v1",
        "OPENAI_API_KEY": "sentinel-secret-value",
        "TERMINAL_CWD": str(ROOT),
    }
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/render_hermes_config.py"),
            "--output",
            str(output),
            "--platform",
            "Linux",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    config = yaml.safe_load(output.read_text())

    assert config["toolsets"]["enabled"] == ["zc-agent-desk"]
    assert config["approvals"]["mode"] == "off"
    assert "test-model" in output.read_text()
    assert "key_env: OPENAI_API_KEY" in output.read_text()
    assert "sentinel-secret-value" not in output.read_text()
