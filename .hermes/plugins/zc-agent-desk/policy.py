from __future__ import annotations

import re
from pathlib import Path


DEVELOPER_TOOLS = {"terminal", "write_file", "patch"}
PATCH_PATH = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


def _path_error(raw_path: str, workspace: Path) -> str | None:
    if not raw_path:
        return "ZC Agent Desk cannot verify an empty developer-tool path"
    root = workspace.expanduser().resolve()
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        return f"ZC Agent Desk blocked path outside workspace: {raw_path}"
    return None


def validate_tool_call(
    tool_name: str,
    args: dict,
    workspace: str | Path,
    platform_name: str,
) -> str | None:
    if tool_name not in DEVELOPER_TOOLS:
        return None
    if platform_name != "Darwin":
        return "ZC Agent Desk developer tools are available only on macOS"

    root = Path(workspace)
    if tool_name == "terminal":
        workdir = args.get("workdir")
        return _path_error(str(workdir), root) if workdir else None
    if tool_name == "write_file":
        return _path_error(str(args.get("path", "")), root)
    if args.get("mode", "replace") == "replace":
        return _path_error(str(args.get("path", "")), root)

    paths = PATCH_PATH.findall(str(args.get("patch", "")))
    if not paths:
        return "ZC Agent Desk cannot verify patch paths"
    for path in paths:
        error = _path_error(path.strip(), root)
        if error:
            return error
    return None
