"""Project-local Hermes tools for ZC Agent Desk."""

from __future__ import annotations

import json


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


def _not_connected(tool_name: str) -> str:
    return json.dumps(
        {
            "error": "zc_agent_desk_backend_unavailable",
            "tool": tool_name,
            "message": "The ZC Agent Desk backend bridge is not configured.",
        }
    )


def query_mock_business(args: dict, **_: object) -> str:
    """Temporary G1 handler; the verified backend bridge is added at G3."""
    return _not_connected("query_mock_business")


def create_todo(args: dict, **_: object) -> str:
    """Temporary G1 handler; approval and persistence are added at G3."""
    return _not_connected("create_todo")


def register(ctx) -> None:
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

