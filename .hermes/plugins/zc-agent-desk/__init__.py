"""Project-local Hermes tools for ZC Agent Desk."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from urllib import error, parse, request

from .policy import DEVELOPER_TOOLS, validate_tool_call


QUERY_MOCK_BUSINESS = {
    "name": "query_mock_business",
    "description": (
        "Look up an internal mock customer order by its exact order ID. "
        "Use this when the user asks about an order, delivery, amount, status, "
        "customer, or account owner."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Exact order ID such as ORD-1001.",
            }
        },
        "required": ["order_id"],
        "additionalProperties": False,
    },
}

CREATE_TODO = {
    "name": "create_todo",
    "description": (
        "Propose a todo for the current employee. This is a write operation "
        "and must wait for explicit user approval before persistence."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Concise todo title."},
            "due_at": {
                "type": "string",
                "description": "Optional ISO-8601 due date or datetime.",
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Optional priority; defaults to medium.",
            },
        },
        "required": ["title"],
        "additionalProperties": False,
    },
}


def _bridge(path: str, *, payload: dict | None = None, timeout: float = 10) -> dict:
    base_url = os.getenv("ZC_AGENT_DESK_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    api_key = os.getenv("HERMES_API_KEY", "")
    if not api_key:
        raise RuntimeError("ZC Agent Desk bridge authentication is not configured")
    body = json.dumps(payload).encode() if payload is not None else None
    bridge_request = request.Request(
        f"{base_url}{path}",
        data=body,
        method="POST" if payload is not None else "GET",
        headers={
            "Content-Type": "application/json",
            "X-ZC-Bridge-Key": api_key,
        },
    )
    try:
        with request.urlopen(bridge_request, timeout=timeout) as response:
            result = json.loads(response.read())
    except (error.HTTPError, error.URLError, TimeoutError) as exc:
        raise RuntimeError("ZC Agent Desk backend bridge is unavailable") from exc
    if not isinstance(result, dict):
        raise RuntimeError("ZC Agent Desk backend returned an invalid response")
    return result


def query_mock_business(args: dict, **_: object) -> str:
    order_id = parse.quote(str(args.get("order_id", "")), safe="")
    return json.dumps(_bridge(f"/api/internal/orders/{order_id}"), ensure_ascii=False)


def create_todo(args: dict, session_id: str = "", **_: object) -> str:
    if not session_id:
        return json.dumps({"error": "missing_session_id"})
    timeout = float(os.getenv("ZC_AGENT_DESK_APPROVAL_TIMEOUT", "310"))
    response = _bridge(
        f"/api/internal/runs/{parse.quote(session_id, safe='')}/proposals",
        payload={"tool": "create_todo", "arguments": args},
        timeout=timeout,
    )
    if not response.get("approved"):
        return json.dumps({"error": "user_rejected", **response.get("result", {})})
    return json.dumps(response.get("result", {}), ensure_ascii=False)


def approve_developer_tool(
    tool_name: str,
    args: dict,
    session_id: str = "",
    tool_call_id: str = "",
    **_: object,
) -> dict | None:
    if tool_name not in DEVELOPER_TOOLS:
        return None
    workspace = Path(os.getenv("TERMINAL_CWD", os.getcwd()))
    policy_error = validate_tool_call(tool_name, args, workspace, platform.system())
    if policy_error:
        return {"action": "block", "message": policy_error}
    if not session_id:
        return {"action": "block", "message": "ZC Agent Desk approval requires a run session"}
    timeout = float(os.getenv("ZC_AGENT_DESK_APPROVAL_TIMEOUT", "310"))
    try:
        response = _bridge(
            f"/api/internal/runs/{parse.quote(session_id, safe='')}/proposals",
            payload={
                "tool": tool_name,
                "arguments": args,
                "proposal_id": tool_call_id,
            },
            timeout=timeout,
        )
    except RuntimeError:
        return {"action": "block", "message": "ZC Agent Desk approval bridge is unavailable"}
    if response.get("approved"):
        return None
    return {"action": "block", "message": "User rejected the developer tool call"}


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", approve_developer_tool)
    ctx.register_tool(
        name="query_mock_business",
        toolset="zc-agent-desk",
        schema=QUERY_MOCK_BUSINESS,
        handler=query_mock_business,
        emoji="📦",
    )
    ctx.register_tool(
        name="create_todo",
        toolset="zc-agent-desk",
        schema=CREATE_TODO,
        handler=create_todo,
        emoji="✅",
    )
