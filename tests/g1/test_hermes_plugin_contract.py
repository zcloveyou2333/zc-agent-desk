from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = PROJECT_ROOT / ".hermes" / "plugins" / "zc-agent-desk"
HERMES_CONFIG = PROJECT_ROOT / "config" / "hermes-config.yaml"


class RecordingContext:
    def __init__(self) -> None:
        self.tools: dict[str, dict] = {}

    def register_tool(self, **definition) -> None:
        self.tools[definition["name"]] = definition


def load_plugin_module():
    spec = importlib.util.spec_from_file_location(
        "zc_agent_desk_hermes_plugin", PLUGIN_ROOT / "__init__.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_declares_the_two_business_tools() -> None:
    manifest = yaml.safe_load((PLUGIN_ROOT / "plugin.yaml").read_text())

    assert manifest["name"] == "zc-agent-desk"
    assert manifest["provides_tools"] == ["query_mock_business", "create_todo"]


def test_plugin_registers_structured_business_tools() -> None:
    context = RecordingContext()

    load_plugin_module().register(context)

    assert set(context.tools) == {"query_mock_business", "create_todo"}
    query_schema = context.tools["query_mock_business"]["schema"]
    todo_schema = context.tools["create_todo"]["schema"]
    assert query_schema["parameters"]["required"] == ["order_id"]
    assert todo_schema["parameters"]["required"] == ["title"]


def test_hermes_profile_explicitly_enables_the_project_plugin() -> None:
    config = yaml.safe_load(HERMES_CONFIG.read_text())

    assert "zc-agent-desk" in config["plugins"]["enabled"]
    assert config["terminal"]["cwd"] == "__ZC_AGENT_DESK_ROOT__"
    api_server = config["gateway"]["platforms"]["api_server"]
    assert api_server["enabled"] is True
    assert api_server["extra"] == {"host": "127.0.0.1", "port": 8642}
