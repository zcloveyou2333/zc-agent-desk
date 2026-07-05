from __future__ import annotations

import asyncio
import time

from fastapi.testclient import TestClient

from zc_agent_desk.app import create_app


class FakeHermes:
    def __init__(self, events: list[dict]):
        self.event_list = events
        self.starts: list[dict] = []
        self.cancelled: list[str] = []

    async def start_run(self, message, *, session_id, conversation_history=None):
        self.starts.append(
            {"message": message, "session_id": session_id, "history": conversation_history or []}
        )
        return f"upstream-{session_id}"

    async def events(self, _run_id):
        for event in self.event_list:
            await asyncio.sleep(0)
            yield event

    async def cancel(self, run_id):
        self.cancelled.append(run_id)


def wait_for_status(client: TestClient, conversation_id: str, run_id: str, status: str):
    for _ in range(100):
        detail = client.get(f"/api/conversations/{conversation_id}").json()
        run = next(item for item in detail["runs"] if item["id"] == run_id)
        if run["status"] == status:
            return detail, run
        time.sleep(0.01)
    raise AssertionError(f"run {run_id} did not reach {status}")


def test_live_runtime_normalizes_events_and_persists_final_message(tmp_path) -> None:
    hermes = FakeHermes(
        [
            {"event": "message.delta", "delta": "订单"},
            {"event": "tool.started", "tool": "query_mock_business", "preview": "ORD-1001"},
            {"event": "tool.completed", "tool": "query_mock_business", "error": False},
            {"event": "message.delta", "delta": "已发货"},
            {"event": "run.completed", "output": "订单 ORD-1001 已发货"},
        ]
    )
    app = create_app(database_path=tmp_path / "live.sqlite3", mode="hermes", hermes_client=hermes)

    with TestClient(app) as client:
        conversation_id = client.post("/api/conversations", json={"title": "live"}).json()["id"]
        client.post(
            f"/api/conversations/{conversation_id}/runs", json={"message": "第一轮"}
        )
        first_detail = client.get(f"/api/conversations/{conversation_id}").json()
        first_run = first_detail["runs"][-1]
        wait_for_status(client, conversation_id, first_run["id"], "completed")

        response = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "查询订单 ORD-1001"},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "running"
        run_id = response.json()["run_id"]
        detail, run = wait_for_status(client, conversation_id, run_id, "completed")

    assert hermes.starts[-1]["session_id"] == run_id
    assert [item["role"] for item in hermes.starts[-1]["history"]] == ["user", "assistant"]
    assert [event["type"] for event in run["events"]] == [
        "message.delta",
        "tool.started",
        "tool.completed",
        "message.delta",
        "message.completed",
    ]
    assert detail["messages"][-1]["content"] == "订单 ORD-1001 已发货"
    assert detail["messages"][-2]["run_id"] == run_id
    assert detail["messages"][-1]["run_id"] == run_id


def test_live_runtime_records_sanitized_failure(tmp_path) -> None:
    hermes = FakeHermes([{"event": "run.failed", "error": "provider exploded"}])
    app = create_app(database_path=tmp_path / "failed.sqlite3", mode="hermes", hermes_client=hermes)

    with TestClient(app) as client:
        conversation_id = client.post("/api/conversations", json={}).json()["id"]
        run_id = client.post(
            f"/api/conversations/{conversation_id}/runs", json={"message": "hello"}
        ).json()["run_id"]
        _, run = wait_for_status(client, conversation_id, run_id, "failed")

    assert run["events"][-1]["type"] == "run.failed"
    assert run["events"][-1]["data"] == {"message": "Hermes run failed"}


def test_live_cancel_forwards_upstream_and_is_idempotent(tmp_path) -> None:
    gate = asyncio.Event()

    class WaitingHermes(FakeHermes):
        async def events(self, _run_id):
            await gate.wait()
            if False:
                yield {}

    hermes = WaitingHermes([])
    app = create_app(database_path=tmp_path / "cancel.sqlite3", mode="hermes", hermes_client=hermes)

    with TestClient(app) as client:
        conversation_id = client.post("/api/conversations", json={}).json()["id"]
        run_id = client.post(
            f"/api/conversations/{conversation_id}/runs", json={"message": "wait"}
        ).json()["run_id"]
        for _ in range(100):
            detail = client.get(f"/api/conversations/{conversation_id}").json()
            run = detail["runs"][-1]
            if run["upstream_run_id"]:
                break
            time.sleep(0.01)
        first = client.post(f"/api/runs/{run_id}/cancel").json()
        second = client.post(f"/api/runs/{run_id}/cancel").json()

    assert hermes.cancelled == [f"upstream-{run_id}"]
    assert first["replayed"] is False
    assert second["replayed"] is True
