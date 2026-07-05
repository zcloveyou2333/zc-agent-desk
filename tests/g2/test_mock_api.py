from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from zc_agent_desk.app import Store, create_app


def make_client(tmp_path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "test.sqlite3"))


def create_conversation(client: TestClient) -> str:
    response = client.post("/api/conversations", json={"title": "测试会话"})
    assert response.status_code == 201
    return response.json()["id"]


def test_initialize_adds_run_id_to_legacy_messages_table(tmp_path) -> None:
    database = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database) as db:
        db.executescript(
            """
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE messages (
                id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL
            );
            INSERT INTO conversations VALUES ('c1', '旧会话', '2026-07-03T00:00:00Z');
            INSERT INTO messages VALUES ('m1', 'c1', 'user', '旧消息', '2026-07-03T00:00:00Z');
            """
        )

    store = Store(database)
    store.initialize()

    with store.connect() as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(messages)")}
        message = db.execute("SELECT content, run_id FROM messages WHERE id='m1'").fetchone()
    assert "run_id" in columns
    assert tuple(message) == ("旧消息", None)


def test_ordinary_reply_uses_conversation_history(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)

        first = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "你好，我叫小雁"},
        )
        second = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "我刚才说我叫什么？"},
        )

        assert first.status_code == 202
        assert second.status_code == 202
        detail = client.get(f"/api/conversations/{conversation_id}").json()
        assert [message["role"] for message in detail["messages"]] == [
            "user",
            "assistant",
            "user",
            "assistant",
        ]
        assert "小雁" in detail["messages"][-1]["content"]


def test_order_query_returns_seeded_order_and_trace(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)
        response = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "帮我查询订单 ORD-1001"},
        )

        assert response.status_code == 202
        run_id = response.json()["run_id"]
        detail = client.get(f"/api/conversations/{conversation_id}").json()
        run = detail["runs"][-1]
        assert run["id"] == run_id
        assert run["status"] == "completed"
        assert [event["type"] for event in run["events"]] == [
            "tool.started",
            "tool.completed",
            "message.delta",
            "message.completed",
        ]
        assert "已发货" in run["events"][-1]["data"]["content"]
        assert detail["messages"][-2]["run_id"] == run_id
        assert detail["messages"][-1]["run_id"] == run_id


def test_missing_order_is_reported_without_failing_run(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)
        response = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "查询订单 ORD-9999"},
        )

        run_id = response.json()["run_id"]
        detail = client.get(f"/api/conversations/{conversation_id}").json()
        run = next(run for run in detail["runs"] if run["id"] == run_id)
        assert run["status"] == "completed"
        assert "没有找到" in detail["messages"][-1]["content"]


def test_todo_is_created_only_after_approval_and_replay_is_idempotent(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)
        response = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "创建待办：周五提交周报"},
        )
        run_id = response.json()["run_id"]

        assert response.json()["status"] == "awaiting_approval"
        assert client.get("/api/todos").json() == []

        approved = client.post(
            f"/api/runs/{run_id}/approval", json={"decision": "approve"}
        )
        replay = client.post(
            f"/api/runs/{run_id}/approval", json={"decision": "approve"}
        )

        assert approved.status_code == 200
        assert approved.json()["status"] == "completed"
        assert replay.status_code == 200
        assert replay.json()["replayed"] is True
        todos = client.get("/api/todos").json()
        assert len(todos) == 1
        assert todos[0]["title"] == "周五提交周报"


def test_rejected_todo_has_no_side_effect(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)
        run_id = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "创建待办：删除旧草稿"},
        ).json()["run_id"]

        rejected = client.post(
            f"/api/runs/{run_id}/approval", json={"decision": "reject"}
        )

        assert rejected.status_code == 200
        assert rejected.json()["status"] == "completed"
        assert client.get("/api/todos").json() == []


def test_completed_sse_replays_only_events_after_last_event_id(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)
        run_id = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "查询订单 ORD-1001"},
        ).json()["run_id"]

        response = client.get(
            f"/api/runs/{run_id}/events", headers={"Last-Event-ID": "2"}
        )

        assert response.status_code == 200
        assert "id: 1\n" not in response.text
        assert "id: 2\n" not in response.text
        assert "id: 3\n" in response.text
        assert "event: message.delta" in response.text
        assert "event: message.completed" in response.text


def test_cancel_is_idempotent(tmp_path) -> None:
    with make_client(tmp_path) as client:
        conversation_id = create_conversation(client)
        run_id = client.post(
            f"/api/conversations/{conversation_id}/runs",
            json={"message": "创建待办：稍后处理"},
        ).json()["run_id"]

        first = client.post(f"/api/runs/{run_id}/cancel")
        second = client.post(f"/api/runs/{run_id}/cancel")

        assert first.json() == {"run_id": run_id, "status": "cancelled", "replayed": False}
        assert second.json() == {"run_id": run_id, "status": "cancelled", "replayed": True}
        assert client.get("/api/todos").json() == []
