from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .hermes import HermesClient


TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def now() -> str:
    return datetime.now(UTC).isoformat()


class ConversationCreate(BaseModel):
    title: str = "新会话"


class RunCreate(BaseModel):
    message: str = Field(min_length=1)


class ApprovalCreate(BaseModel):
    decision: str


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                    status TEXT NOT NULL, pending_tool TEXT, pending_args TEXT,
                    upstream_run_id TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    run_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    type TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(run_id, sequence),
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    run_id TEXT PRIMARY KEY, decision TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                CREATE TABLE IF NOT EXISTS todos (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                    due_at TEXT, priority TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY, status TEXT NOT NULL, item TEXT NOT NULL,
                    amount REAL NOT NULL, updated_at TEXT NOT NULL
                );
                """
            )
            db.execute(
                """INSERT OR IGNORE INTO orders(id, status, item, amount, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                ("ORD-1001", "已发货", "轻量办公背包", 299.0, "2026-07-02T10:00:00+08:00"),
            )
            run_columns = {row[1] for row in db.execute("PRAGMA table_info(runs)").fetchall()}
            if "upstream_run_id" not in run_columns:
                db.execute("ALTER TABLE runs ADD COLUMN upstream_run_id TEXT")

    def create_conversation(self, title: str) -> dict[str, Any]:
        item = {"id": uuid.uuid4().hex, "title": title.strip() or "新会话", "created_at": now()}
        with self.connect() as db:
            db.execute(
                "INSERT INTO conversations(id, title, created_at) VALUES (:id, :title, :created_at)",
                item,
            )
        return item

    def add_message(self, conversation_id: str, role: str, content: str) -> dict[str, Any]:
        item = {
            "id": uuid.uuid4().hex,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": now(),
        }
        with self.connect() as db:
            db.execute(
                """INSERT INTO messages(id, conversation_id, role, content, created_at)
                   VALUES (:id, :conversation_id, :role, :content, :created_at)""",
                item,
            )
        return item

    def messages(self, conversation_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id, role, content, created_at FROM messages WHERE conversation_id=? ORDER BY rowid",
                (conversation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_run(self, conversation_id: str) -> str:
        run_id = uuid.uuid4().hex
        timestamp = now()
        with self.connect() as db:
            db.execute(
                """INSERT INTO runs(id, conversation_id, status, created_at, updated_at)
                   VALUES (?, ?, 'running', ?, ?)""",
                (run_id, conversation_id, timestamp, timestamp),
            )
        return run_id

    def set_run(self, run_id: str, status: str, tool: str | None = None, args: dict | None = None) -> None:
        with self.connect() as db:
            db.execute(
                """UPDATE runs SET status=?, pending_tool=?, pending_args=?, updated_at=? WHERE id=?""",
                (status, tool, json.dumps(args, ensure_ascii=False) if args else None, now(), run_id),
            )

    def set_upstream_run(self, run_id: str, upstream_run_id: str) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET upstream_run_id=?, updated_at=? WHERE id=?",
                (upstream_run_id, now(), run_id),
            )

    def run(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def add_event(self, run_id: str, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as db:
            sequence = db.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM events WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            event = {
                "run_id": run_id,
                "sequence": sequence,
                "type": event_type,
                "data": data,
                "created_at": now(),
            }
            db.execute(
                "INSERT INTO events(run_id, sequence, type, data, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, sequence, event_type, json.dumps(data, ensure_ascii=False), event["created_at"]),
            )
        return event

    def events(self, run_id: str, after: int = 0) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE run_id=? AND sequence>? ORDER BY sequence",
                (run_id, after),
            ).fetchall()
        return [dict(row) | {"data": json.loads(row["data"])} for row in rows]

    def conversation(self, conversation_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            conversation = db.execute(
                "SELECT * FROM conversations WHERE id=?", (conversation_id,)
            ).fetchone()
            if not conversation:
                return None
            run_rows = db.execute(
                "SELECT * FROM runs WHERE conversation_id=? ORDER BY rowid", (conversation_id,)
            ).fetchall()
        runs = []
        for row in run_rows:
            run = dict(row)
            run["pending_args"] = json.loads(run["pending_args"]) if run["pending_args"] else None
            run["events"] = self.events(run["id"])
            runs.append(run)
        return dict(conversation) | {"messages": self.messages(conversation_id), "runs": runs}

    def order(self, order_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return dict(row) if row else None

    def approval(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM approvals WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def record_approval(self, run_id: str, decision: str) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO approvals(run_id, decision, created_at) VALUES (?, ?, ?)",
                (run_id, decision, now()),
            )

    def create_todo(self, run_id: str, args: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                """INSERT OR IGNORE INTO todos(id, run_id, title, due_at, priority, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (uuid.uuid4().hex, run_id, args["title"], args.get("due_at"), args.get("priority", "normal"), now()),
            )

    def todos(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id, title, due_at, priority, created_at FROM todos ORDER BY rowid DESC"
            ).fetchall()
        return [dict(row) for row in rows]


def assistant_message(store: Store, run_id: str, conversation_id: str, content: str) -> None:
    store.add_message(conversation_id, "assistant", content)
    store.add_event(run_id, "message.delta", {"delta": content})
    store.add_event(run_id, "message.completed", {"content": content})
    store.set_run(run_id, "completed")


def execute_mock(store: Store, conversation_id: str, run_id: str, message: str) -> str:
    order_match = re.search(r"ORD-\d+", message.upper())
    if order_match:
        order_id = order_match.group(0)
        store.add_event(run_id, "tool.started", {"tool": "query_mock_business", "arguments": {"order_id": order_id}})
        order = store.order(order_id)
        store.add_event(run_id, "tool.completed", {"tool": "query_mock_business", "result": order})
        if order:
            content = f"订单 {order_id} 当前状态：{order['status']}，商品：{order['item']}，金额：¥{order['amount']:.2f}。"
        else:
            content = f"没有找到订单 {order_id}，请检查订单号。"
        assistant_message(store, run_id, conversation_id, content)
        return "completed"

    todo_match = re.search(r"(?:创建|添加)(?:一个)?待办[：:]?\s*(.+)", message)
    if todo_match:
        args = {"title": todo_match.group(1).strip(), "priority": "normal"}
        store.add_event(run_id, "tool.started", {"tool": "create_todo", "arguments": args})
        store.add_event(run_id, "approval.required", {"tool": "create_todo", "arguments": args})
        store.set_run(run_id, "awaiting_approval", "create_todo", args)
        return "awaiting_approval"

    history = store.messages(conversation_id)
    if "叫什么" in message:
        names = [match.group(1) for item in history[:-1] if (match := re.search(r"我叫([^，。！？\s]+)", item["content"]))]
        content = f"你刚才说你叫{names[-1]}。" if names else "你还没有告诉我名字。"
    else:
        content = "你好，我是 ZC Agent Desk Mock 助手。我已记住这轮对话。"
    assistant_message(store, run_id, conversation_id, content)
    return "completed"


def create_app(
    database_path: str | Path = "./data/zc-agent-desk.sqlite3",
    *,
    mode: str | None = None,
    hermes_client: Any | None = None,
) -> FastAPI:
    store = Store(Path(database_path))
    runtime_mode = mode or os.getenv("APP_MODE", "mock")
    if runtime_mode not in {"mock", "hermes"}:
        raise ValueError("APP_MODE must be mock or hermes")
    if runtime_mode == "hermes" and hermes_client is None:
        hermes_client = HermesClient(
            os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8642"),
            os.getenv("HERMES_API_KEY", ""),
        )
    tasks: set[asyncio.Task] = set()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        store.initialize()
        yield
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="ZC Agent Desk API", lifespan=lifespan)
    app.state.store = store
    app.state.mode = runtime_mode
    app.state.hermes_client = hermes_client
    app.state.tasks = tasks
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": runtime_mode}

    @app.post("/api/conversations", status_code=201)
    def create_conversation(body: ConversationCreate) -> dict[str, Any]:
        return store.create_conversation(body.title)

    @app.get("/api/conversations")
    def list_conversations() -> list[dict[str, Any]]:
        with store.connect() as db:
            rows = db.execute("SELECT * FROM conversations ORDER BY rowid DESC").fetchall()
        return [dict(row) for row in rows]

    @app.get("/api/conversations/{conversation_id}")
    def get_conversation(conversation_id: str) -> dict[str, Any]:
        result = store.conversation(conversation_id)
        if not result:
            raise HTTPException(404, "Conversation not found")
        return result

    async def consume_hermes_run(
        local_run_id: str,
        conversation_id: str,
        message: str,
        history: list[dict[str, str]],
    ) -> None:
        try:
            upstream_run_id = await hermes_client.start_run(
                message,
                session_id=local_run_id,
                conversation_history=history,
            )
            store.set_upstream_run(local_run_id, upstream_run_id)
            async for event in hermes_client.events(upstream_run_id):
                event_type = event.get("event")
                if event_type == "message.delta":
                    store.add_event(local_run_id, "message.delta", {"delta": event.get("delta", "")})
                elif event_type in {"tool.started", "tool.completed"}:
                    data = {
                        key: event[key]
                        for key in ("tool", "preview", "duration", "error")
                        if key in event
                    }
                    store.add_event(local_run_id, event_type, data)
                elif event_type == "approval.request":
                    args = {key: value for key, value in event.items() if key not in {"event", "run_id", "timestamp"}}
                    store.add_event(local_run_id, "approval.required", args)
                    store.set_run(local_run_id, "awaiting_approval", str(event.get("tool") or "terminal"), args)
                elif event_type == "run.completed":
                    output = str(event.get("output") or "")
                    store.add_message(conversation_id, "assistant", output)
                    store.add_event(local_run_id, "message.completed", {"content": output})
                    store.set_run(local_run_id, "completed")
                    return
                elif event_type == "run.failed":
                    store.add_event(local_run_id, "run.failed", {"message": "Hermes run failed"})
                    store.set_run(local_run_id, "failed")
                    return
        except Exception:
            if store.run(local_run_id) and store.run(local_run_id)["status"] not in TERMINAL_STATUSES:
                store.add_event(local_run_id, "run.failed", {"message": "Hermes is unavailable"})
                store.set_run(local_run_id, "failed")

    @app.post("/api/conversations/{conversation_id}/runs", status_code=202)
    async def create_run(conversation_id: str, body: RunCreate) -> dict[str, str]:
        if not store.conversation(conversation_id):
            raise HTTPException(404, "Conversation not found")
        store.add_message(conversation_id, "user", body.message)
        run_id = store.create_run(conversation_id)
        if runtime_mode == "mock":
            status = execute_mock(store, conversation_id, run_id, body.message)
        else:
            history = [
                {"role": item["role"], "content": item["content"]}
                for item in store.messages(conversation_id)[:-1]
            ]
            task = asyncio.create_task(
                consume_hermes_run(run_id, conversation_id, body.message, history)
            )
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            status = "running"
        return {"run_id": run_id, "status": status}

    @app.get("/api/runs/{run_id}/events")
    async def run_events(
        run_id: str,
        request: Request,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ) -> StreamingResponse:
        if not store.run(run_id):
            raise HTTPException(404, "Run not found")
        cursor = int(last_event_id or 0)

        async def stream():
            nonlocal cursor
            while True:
                for event in store.events(run_id, cursor):
                    cursor = event["sequence"]
                    payload = json.dumps(event["data"], ensure_ascii=False)
                    yield f"id: {cursor}\nevent: {event['type']}\ndata: {payload}\n\n"
                run = store.run(run_id)
                if run and run["status"] in TERMINAL_STATUSES:
                    break
                if await request.is_disconnected():
                    break
                yield ": keepalive\n\n"
                await asyncio.sleep(0.1)

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.post("/api/runs/{run_id}/approval")
    def approve_run(run_id: str, body: ApprovalCreate) -> dict[str, Any]:
        if body.decision not in {"approve", "reject"}:
            raise HTTPException(422, "Decision must be approve or reject")
        run = store.run(run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        existing = store.approval(run_id)
        if existing:
            return {"run_id": run_id, "status": store.run(run_id)["status"], "replayed": True}
        if run["status"] != "awaiting_approval":
            raise HTTPException(409, "Run is not awaiting approval")
        store.record_approval(run_id, body.decision)
        args = json.loads(run["pending_args"])
        if body.decision == "approve":
            store.create_todo(run_id, args)
            result = {"created": True, "title": args["title"]}
            content = f"待办“{args['title']}”已创建。"
        else:
            result = {"created": False, "reason": "rejected"}
            content = f"已拒绝创建待办“{args['title']}”。"
        store.add_event(run_id, "tool.completed", {"tool": "create_todo", "result": result})
        assistant_message(store, run_id, run["conversation_id"], content)
        return {"run_id": run_id, "status": "completed", "replayed": False}

    @app.post("/api/runs/{run_id}/cancel")
    async def cancel_run(run_id: str) -> dict[str, Any]:
        run = store.run(run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        replayed = run["status"] == "cancelled"
        if not replayed:
            if run["status"] in TERMINAL_STATUSES:
                return {"run_id": run_id, "status": run["status"], "replayed": True}
            if runtime_mode == "hermes" and run.get("upstream_run_id"):
                await hermes_client.cancel(run["upstream_run_id"])
            store.set_run(run_id, "cancelled")
        return {"run_id": run_id, "status": "cancelled", "replayed": replayed}

    @app.get("/api/todos")
    def get_todos() -> list[dict[str, Any]]:
        return store.todos()

    return app


app = create_app()
