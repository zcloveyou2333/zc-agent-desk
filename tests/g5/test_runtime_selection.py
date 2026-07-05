from __future__ import annotations

import asyncio
import sqlite3

from fastapi.testclient import TestClient

from zc_agent_desk.app import Store, create_app


class CompletingHermes:
    async def start_run(self, message, *, session_id, conversation_history=None):
        return f"upstream-{session_id}"

    async def events(self, _run_id):
        await asyncio.sleep(0)
        yield {"event": "run.completed", "output": "Real Agent 已完成"}

    async def cancel(self, _run_id):
        return None


def test_initialize_adds_runtime_mode_to_legacy_runs(tmp_path) -> None:
    database = tmp_path / "legacy.sqlite3"
    store = Store(database)
    store.initialize()
    with store.connect() as db:
        db.execute(
            "INSERT INTO conversations(id,title,created_at) VALUES ('c1','legacy','now')"
        )
        db.execute("DROP TABLE runs")
        db.execute(
            """CREATE TABLE runs (
                id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, status TEXT NOT NULL,
                pending_tool TEXT, pending_args TEXT, upstream_run_id TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )"""
        )
        db.execute(
            "INSERT INTO runs VALUES ('r1','c1','completed',NULL,NULL,NULL,'now','now')"
        )

    store.initialize()

    with store.connect() as db:
        row = db.execute("SELECT runtime_mode FROM runs WHERE id='r1'").fetchone()
    assert row[0] == "workflow"


def test_conversation_can_mix_workflow_and_real_runs(tmp_path) -> None:
    app = create_app(
        database_path=tmp_path / "mixed.sqlite3",
        mode="auto",
        hermes_client=CompletingHermes(),
        hermes_enabled=True,
    )
    with TestClient(app) as client:
        conversation_id = client.post("/api/conversations", json={}).json()["id"]
        workflow = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "分析 2026-06 飘窗垫的关键词需求", "mode": "workflow"},
        )
        real = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "用真实模型回答", "mode": "hermes"},
        )
        assert workflow.status_code == 202
        assert real.status_code == 202
        for _ in range(100):
            detail = client.get(f"/api/conversations/{conversation_id}").json()
            if detail["runs"][-1]["status"] == "completed":
                break
        else:
            raise AssertionError("real run did not complete")

    assert [run["runtime_mode"] for run in detail["runs"]] == ["workflow", "hermes"]
    workflow_events = detail["runs"][0]["events"]
    assert len([event for event in workflow_events if event["type"] == "tool.started"]) == 6
    assert "关键词分析" in detail["messages"][1]["content"]


def test_mock_alias_is_persisted_as_workflow(tmp_path) -> None:
    with TestClient(create_app(database_path=tmp_path / "alias.sqlite3", mode="mock")) as client:
        conversation_id = client.post("/api/conversations", json={}).json()["id"]
        response = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "你好", "mode": "mock"},
        )
        detail = client.get(f"/api/conversations/{conversation_id}").json()

    assert response.status_code == 202
    assert detail["runs"][-1]["runtime_mode"] == "workflow"


def test_unavailable_real_agent_returns_503_without_persistence(tmp_path) -> None:
    app = create_app(
        database_path=tmp_path / "unavailable.sqlite3",
        mode="auto",
        hermes_enabled=False,
    )
    with TestClient(app) as client:
        conversation_id = client.post("/api/conversations", json={}).json()["id"]
        response = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "hello", "mode": "hermes"},
        )
        detail = client.get(f"/api/conversations/{conversation_id}").json()
        health = client.get("/api/health").json()

    assert response.status_code == 503
    assert response.json()["detail"] == "Real Agent 尚未配置"
    assert detail["messages"] == []
    assert detail["runs"] == []
    assert health["runtimes"] == {
        "workflow": {"available": True},
        "hermes": {"available": False, "reason": "Real Agent 尚未配置"},
    }
