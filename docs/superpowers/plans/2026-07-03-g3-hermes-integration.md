# G3 Hermes 集成实施计划

> **执行要求：** 使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development`，按任务逐项执行并验证。

**目标：** 把持久化 FastAPI 应用连接到 Hermes 0.18，使实时模型自主选择工具，同时沿用公开 API、审批和 React UI。

**架构：** FastAPI 异步启动 Hermes `/v1/runs`，把 sidecar SSE 统一为本地事件并写入 SQLite。
本地 run ID 作为 `session_id` 传递，项目插件通过带认证桥接调用业务工具和阻塞审批，不修改 Hermes 核心。

**技术栈：** FastAPI、SQLite、HTTPX、Hermes 项目插件、pytest、macOS `sandbox-exec`。

---

### 任务 1：Hermes Client 与事件标准化

**文件：** `backend/zc_agent_desk/hermes.py`、`tests/g3/test_hermes_client.py`

- [ ] 使用 `httpx.MockTransport` 先写失败测试，覆盖运行创建、`session_id`、历史消息、Bearer 认证、SSE、审批、取消和上游错误。
- [ ] 实现 `HermesClient.start_run`、`events`、`approve` 和 `cancel`，不耦合 SQLite。
- [ ] 把 Hermes 事件映射为公开 `message.delta`、`tool.started`、`tool.completed`、`message.completed` 和 `run.failed`。
- [ ] 运行：`.venv/bin/pytest -q tests/g3/test_hermes_client.py`

### 任务 2：实时应用 Runtime

**文件：** `backend/zc_agent_desk/app.py`、`tests/g3/test_live_runtime.py`

- [ ] 为 `create_app` 增加模式和可注入 Hermes Client，保留 Mock 行为。
- [ ] 后台消费 Hermes SSE，持久化上游 run ID、统一事件和最终消息。
- [ ] 审批与取消转发到 sidecar；终止状态必须幂等。
- [ ] 测试助手回复、失败脱敏、取消和刷新恢复。

### 任务 3：带认证的业务工具桥接

**文件：** `.hermes/plugins/zc-agent-desk/`、`backend/zc_agent_desk/app.py`、`tests/g3/test_business_bridge.py`

- [ ] 注册 `query_mock_business` 和 `create_todo` Schema。
- [ ] 订单读取直接执行；未知订单返回 HTTP 200 和 `{found: false}`。
- [ ] 待办提案写入 `approval.required` 后阻塞，批准时事务性创建一次，拒绝/超时/重放不产生副作用。
- [ ] 使用 `HERMES_API_KEY` 保护内部桥接接口。

### 任务 4：开发者工具审批与路径策略

**文件：** 项目插件 Hook、`backend/zc_agent_desk/security.py`、`config/macos-hermes.sb`

- [ ] `pre_tool_call` 对每次 terminal、write、patch 执行应用审批，不依赖 Hermes 危险命令分类。
- [ ] 路径经过 realpath 和 symlink 越界检查，拒绝绝对路径、路径穿越和工作区外修改。
- [ ] macOS 使用 `sandbox-exec` 约束；其他系统不暴露开发者工具。
- [ ] 原生 Hermes 审批设为 `off`，避免双重提示。

### 任务 5：实时验证与 Gate 记录

- [ ] 验证普通回复、多轮历史和模型自主订单工具调用。
- [ ] 验证待办审批只持久化一次，终端拒绝阻止执行。
- [ ] 验证中转超时转为脱敏失败状态。
- [ ] 运行：

```bash
.venv/bin/pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run build
```

- [ ] 更新 README、架构、进度和 AI 协作记录后提交 G3。
