from __future__ import annotations

import importlib.util
import json
import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from zc_agent_desk.app import create_app


PLUGIN = Path(__file__).resolve().parents[2] / ".hermes/plugins/zc-agent-desk/__init__.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("zc_bridge_plugin", PLUGIN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_run(app) -> tuple[str, str]:
    store = app.state.store
    conversation_id = store.create_conversation("bridge")["id"]
    run_id = store.create_run(conversation_id)
    return conversation_id, run_id


def test_internal_order_bridge_requires_auth_and_returns_seeded_data(tmp_path) -> None:
    app = create_app(database_path=tmp_path / "bridge.sqlite3", bridge_key="bridge-secret")
    with TestClient(app) as client:
        assert client.get("/api/internal/orders/ORD-1001").status_code == 401
        response = client.get(
            "/api/internal/orders/ORD-1001", headers={"X-ZC-Bridge-Key": "bridge-secret"}
        )
        missing = client.get(
            "/api/internal/orders/ORD-9999", headers={"X-ZC-Bridge-Key": "bridge-secret"}
        )

    assert response.status_code == 200
    assert response.json()["found"] is True
    assert response.json()["order"]["status"] == "已发货"
    assert missing.status_code == 200
    assert missing.json() == {"found": False, "order_id": "ORD-9999"}


def test_todo_proposal_blocks_until_approval_then_returns_persisted_result(tmp_path) -> None:
    app = create_app(
        database_path=tmp_path / "approve.sqlite3",
        mode="hermes",
        bridge_key="bridge-secret",
        proposal_timeout=2,
    )
    result: dict = {}

    with TestClient(app) as client:
        _, run_id = seed_run(app)

        def propose() -> None:
            response = client.post(
                f"/api/internal/runs/{run_id}/proposals",
                headers={"X-ZC-Bridge-Key": "bridge-secret"},
                json={"tool": "create_todo", "arguments": {"title": "提交周报", "priority": "high"}},
            )
            result.update({"status": response.status_code, "body": response.json()})

        thread = threading.Thread(target=propose)
        thread.start()
        for _ in range(100):
            if app.state.store.run(run_id)["status"] == "awaiting_approval":
                break
            time.sleep(0.01)

        assert app.state.store.todos() == []
        approval = client.post(
            f"/api/runs/{run_id}/approval", json={"decision": "approve"}
        )
        thread.join(timeout=2)

        assert approval.json()["status"] == "running"
        assert not thread.is_alive()

    assert result == {
        "status": 200,
        "body": {"approved": True, "result": {"created": True, "title": "提交周报"}},
    }
    assert [todo["title"] for todo in app.state.store.todos()] == ["提交周报"]


def test_rejected_proposal_has_no_side_effect_and_replay_is_idempotent(tmp_path) -> None:
    app = create_app(
        database_path=tmp_path / "reject.sqlite3",
        mode="hermes",
        bridge_key="secret",
        proposal_timeout=2,
    )
    responses: list[dict] = []

    with TestClient(app) as client:
        _, run_id = seed_run(app)

        def propose() -> None:
            response = client.post(
                f"/api/internal/runs/{run_id}/proposals",
                headers={"X-ZC-Bridge-Key": "secret"},
                json={"tool": "create_todo", "arguments": {"title": "不应创建"}},
            )
            responses.append(response.json())

        thread = threading.Thread(target=propose)
        thread.start()
        for _ in range(100):
            if app.state.store.run(run_id)["status"] == "awaiting_approval":
                break
            time.sleep(0.01)
        first = client.post(f"/api/runs/{run_id}/approval", json={"decision": "reject"})
        replay = client.post(f"/api/runs/{run_id}/approval", json={"decision": "reject"})
        thread.join(timeout=2)

    assert first.json()["replayed"] is False
    assert replay.json()["replayed"] is True
    assert responses == [{"approved": False, "result": {"created": False, "reason": "rejected"}}]
    assert app.state.store.todos() == []


def test_proposal_timeout_does_not_create_todo(tmp_path) -> None:
    app = create_app(
        database_path=tmp_path / "timeout.sqlite3",
        mode="hermes",
        bridge_key="secret",
        proposal_timeout=0.01,
    )
    with TestClient(app) as client:
        _, run_id = seed_run(app)
        response = client.post(
            f"/api/internal/runs/{run_id}/proposals",
            headers={"X-ZC-Bridge-Key": "secret"},
            json={"tool": "create_todo", "arguments": {"title": "超时"}},
        )
    assert response.status_code == 408
    assert app.state.store.todos() == []


def test_plugin_uses_session_id_and_bridge_auth(monkeypatch) -> None:
    plugin = load_plugin()
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def read(self):
            return json.dumps(
                {"approved": True, "result": {"created": True, "title": "插件待办"}}
            ).encode()

    def fake_urlopen(request, timeout):
        captured.update(
            {
                "url": request.full_url,
                "key": request.headers["X-zc-bridge-key"],
                "body": json.loads(request.data),
                "timeout": timeout,
            }
        )
        return Response()

    monkeypatch.setenv("ZC_AGENT_DESK_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("HERMES_API_KEY", "bridge-secret")
    monkeypatch.setattr(plugin.request, "urlopen", fake_urlopen)

    result = json.loads(plugin.create_todo({"title": "插件待办"}, session_id="local-run"))

    assert captured["url"].endswith("/api/internal/runs/local-run/proposals")
    assert captured["key"] == "bridge-secret"
    assert captured["body"]["tool"] == "create_todo"
    assert result == {"created": True, "title": "插件待办"}
