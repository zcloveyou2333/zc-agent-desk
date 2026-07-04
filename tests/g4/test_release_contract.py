from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_release_check():
    path = ROOT / "scripts/release_check.py"
    spec = importlib.util.spec_from_file_location("release_check", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_check_rejects_private_absolute_paths(tmp_path: Path) -> None:
    module = load_release_check()
    public_file = tmp_path / "README.md"
    public_file.write_text("cd " + "/".join(["", "Users", "example", "private-project"]) + "\n")

    findings = module.scan_text_files([public_file])

    assert findings == [f"{public_file}:1: contains a macOS user path"]


def test_hermes_lock_identifies_an_immutable_upstream_commit() -> None:
    module = load_release_check()

    lock = module.read_lock(ROOT / "config/hermes-source.lock")

    assert lock["source"] == "https://github.com/NousResearch/hermes-agent.git"
    assert lock["commit"] == "5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37"


def test_environment_example_does_not_require_a_machine_specific_workspace() -> None:
    env_example = (ROOT / ".env.example").read_text()

    mac_user_prefix = "/" + "Users" + "/"
    assert "TERMINAL_CWD=" + mac_user_prefix not in env_example
    assert "TERMINAL_CWD=" not in env_example
