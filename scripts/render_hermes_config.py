#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "config/hermes-config.yaml"


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Render isolated Hermes runtime config")
    parser.add_argument("--output", type=Path, default=ROOT / ".hermes/runtime/config.yaml")
    parser.add_argument("--platform", default=platform.system())
    args = parser.parse_args()

    rendered = (
        TEMPLATE.read_text()
        .replace("__MODEL_NAME__", required_env("MODEL_NAME"))
        .replace("__OPENAI_BASE_URL__", required_env("OPENAI_BASE_URL"))
        .replace("__ZC_AGENT_DESK_ROOT__", required_env("TERMINAL_CWD"))
    )
    config = yaml.safe_load(rendered)
    config["approvals"]["mode"] = "off"
    if args.platform != "Darwin":
        config["toolsets"]["enabled"] = ["zc-agent-desk"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
