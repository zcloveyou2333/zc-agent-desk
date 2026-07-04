from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from zc_agent_desk.hermes import HermesClient, HermesUnavailable


def test_client_uses_auth_session_history_and_parses_sse() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/runs":
            body = json.loads(request.content)
            assert body == {
                "input": "查询订单 ORD-1001",
                "session_id": "local-run-1",
                "conversation_history": [{"role": "user", "content": "你好"}],
            }
            return httpx.Response(202, json={"run_id": "hermes-run-1", "status": "started"})
        if request.url.path.endswith("/events"):
            return httpx.Response(
                200,
                text=(
                    'data: {"event":"message.delta","delta":"已"}\n\n'
                    ': keepalive\n\n'
                    'data: {"event":"run.completed","output":"已发货"}\n\n'
                ),
                headers={"Content-Type": "text/event-stream"},
            )
        raise AssertionError(request.url)

    async def scenario() -> list[dict]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://hermes.test"
        ) as http:
            client = HermesClient("http://hermes.test", "local-secret", http=http)
            run_id = await client.start_run(
                "查询订单 ORD-1001",
                session_id="local-run-1",
                conversation_history=[{"role": "user", "content": "你好"}],
            )
            assert run_id == "hermes-run-1"
            return [event async for event in client.events(run_id)]

    events = asyncio.run(scenario())

    assert [event["event"] for event in events] == ["message.delta", "run.completed"]
    assert all(request.headers["authorization"] == "Bearer local-secret" for request in requests)


def test_approval_and_cancel_translate_to_hermes_protocol() -> None:
    calls: list[tuple[str, dict]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, json.loads(request.content or b"{}")))
        return httpx.Response(200, json={"ok": True})

    async def scenario() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://hermes.test"
        ) as http:
            client = HermesClient("http://hermes.test", "secret", http=http)
            await client.approve("upstream", "approve")
            await client.approve("upstream", "reject")
            await client.cancel("upstream")

    asyncio.run(scenario())

    assert calls == [
        ("/v1/runs/upstream/approval", {"choice": "once"}),
        ("/v1/runs/upstream/approval", {"choice": "deny"}),
        ("/v1/runs/upstream/stop", {}),
    ]


def test_upstream_errors_are_sanitized() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="secret provider diagnostic")

    async def scenario() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://hermes.test"
        ) as http:
            client = HermesClient("http://hermes.test", "secret", http=http)
            await client.start_run("hello", session_id="local")

    with pytest.raises(HermesUnavailable, match="Hermes returned HTTP 401") as caught:
        asyncio.run(scenario())
    assert "provider diagnostic" not in str(caught.value)
