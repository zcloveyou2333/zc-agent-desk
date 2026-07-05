# ZC Agent Desk

> 由 zcloveyou 构建

ZC Agent Desk 是一个内部员工 Chatbot MVP，用于展示多轮对话、模型自主选择工具、
写操作显式审批、零 Key 确定性运行，以及可选的 Hermes Agent Runtime。

## 这个 MVP 证明了什么

本次笔试要求的是一个可在本地运行的员工 Chatbot，而不是生产平台。因此本版本聚焦一条
完整纵向链路：持久化多轮聊天、Agent 选择业务工具、写入前审批、事件 Trace、故障处理
和零 Key 验收。登录、线上部署、RAG、多用户权限和复杂编排均明确排除在范围之外。

## 运行模式

- **Workflow**：笔试要求的 Mock 实现。它离线、确定性运行且不需要 API Key。本版本包含
  正式命名的 `关键词分析` Workflow，以及订单、待办和上下文流程。
- **Real Agent**：通过固定版本的 Hermes sidecar 调用兼容 OpenAI Chat Completions 的
  实时模型。两种 Runtime 共用相同的 FastAPI API、SQLite 状态、审批卡片和 Trace UI。

输入框可按消息切换 Runtime，因此同一会话可以同时包含 Workflow 和 Real Agent 的运行，
不需要重启服务。每张运行卡都会记录实际使用的 Runtime。

## 快速启动：Workflow 模式（零 Key Mock）

环境要求：Python 3.11 或更高版本、Node.js 20 或更高版本。Mock 模式不会读取
`OPENAI_API_KEY`，不会启动 Hermes，也不需要 `.env`。

```bash
git clone https://github.com/zcloveyou2333/zc-agent-desk.git
cd zc-agent-desk
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix frontend ci
./scripts/dev.sh
```

浏览器打开 <http://127.0.0.1:5173>。后端监听 <http://127.0.0.1:8000>；
Vite 会把 `/api` 请求代理到后端。

推荐演示提示词：

- `分析 2026年6月飘窗垫的关键词需求`
- `分析 2026-06 办公背包的关键词需求`
- 先输入 `你好，我叫小雁`，再输入 `我刚才说我叫什么？`
- `查询订单 ORD-1001`
- `查询订单 ORD-9999`
- `创建待办：周五提交周报`，然后批准或拒绝对话中的审批卡片

SQLite 数据保存在 `data/zc-agent-desk.sqlite3`，刷新页面后仍会保留。只有在确实需要
全新演示数据时，才删除这个已被 Git 忽略的文件。

关键词 Workflow 使用合成数据，并生成六个可见 Trace 步骤：意图识别、参数提取、数据查询、
八大需求分类、趋势计算和结果渲染。

## 同时启动两种 Runtime

Hermes 模式还需要 Git 和固定版本的 Hermes 源码。安装脚本会检出不可变 commit
`5445e42b`，验证影响兼容性的关键文件哈希，并安装到已被 Git 忽略的 `.vendor/` 目录。

```bash
./scripts/setup_hermes.sh
cp .env.example .env
# 编辑 .env，然后执行 openssl rand -hex 32 生成 HERMES_API_KEY
./scripts/dev.sh
```

为支持结构化 `tool_calls` 的 OpenAI-compatible Chat Completions 接口配置
`OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `MODEL_NAME`。`HERMES_API_KEY` 是 FastAPI
与本机 Hermes sidecar 之间共享的随机桥接密钥，不是模型供应商 Key。不要把这些值粘贴到
源码中，也不要提交 `.env`。

使用模板默认值 `APP_MODE=auto` 时，脚本会把不含密钥的隔离配置渲染到
`.hermes/runtime`，启动 FastAPI 和 React，并在配置完整时启动 Hermes。可以通过输入框上方
按钮切换 Workflow 与 Real Agent。macOS 上的 Hermes 会在项目跟踪的 `sandbox-exec`
策略下运行；其他系统的配置会移除终端和文件工具，但保留两个核心业务工具。

仍可使用显式覆盖：`APP_MODE=mock` 只启动 Workflow；`APP_MODE=hermes` 要求 Hermes
配置完整，缺失时快速失败。`mock` 是兼容性名称，产品 UI 中显示为 Workflow。

Hermes 演示提示词：

- `请查询订单 ORD-1001，并告诉我状态`
- `请直接使用 create_todo 工具创建待办：检查G3审批。不要调用其他工具。`
- `请只使用 terminal 工具执行 pwd，不要使用其他工具。`

后两个提示词会停在对话中的审批卡片。待办获得批准后只会持久化一次，随后 Hermes 才会收到
工具结果。项目插件会为每次开发者工具调用执行审批；Hermes 原生危险命令审批已关闭，避免出现
两次审批。

## 验证

```bash
.venv/bin/pytest -q
cd frontend
npm test -- --run
npm run build
cd ..
./scripts/setup_hermes.sh --verify-only  # 安装 Hermes 后执行
.venv/bin/python scripts/release_check.py
```

当前公开应用 API 包括：

- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{id}`
- `POST /api/conversations/{id}/runs`
- `GET /api/runs/{run_id}/events`
- `POST /api/runs/{run_id}/approval`
- `POST /api/runs/{run_id}/cancel`
- `GET /api/todos`

前端提交运行请求，可重连 SSE 传递统一事件，SQLite 是刷新恢复的事实来源。Workflow 模式由
显式确定性注册表和路由选择具名 Workflow 或业务流程；Real Agent 模式由模型选择工具，
插件通过带认证的 FastAPI 桥接调用，并在写操作或开发者操作执行前阻塞等待审批。工具结果会在
最终回复生成前返回 Runtime。

更多信息见[架构说明](docs/ARCHITECTURE.md)、[设计说明](docs/DESIGN.md)、
[决策记录](docs/DECISIONS.md)、[AI 协作记录](docs/AI_COLLABORATION.md)和
[录屏检查清单](docs/RECORDING.md)。

## AI 工具如何参与项目

本项目主要使用 **OpenAI Codex** 作为结对开发 Agent，并使用 **ChatGPT** 辅助早期方案讨论。
AI 参与了需求拆解、架构比较、实施计划、测试驱动开发、Hermes 技术探针、真实 API 调试、
浏览器验收、故障定位、文档整理和发布检查。关键设计与每次行为变更均由自动化测试或实际运行验证，
而不是直接接受生成结果。

具体采纳、修改和拒绝记录见 [AI 协作记录](docs/AI_COLLABORATION.md)。其中包括拒绝重构 Hermes
核心、拒绝把 `cwd` 伪装成沙箱、保留零 Key Mock、修正 Hermes 插件与审批配置，以及根据真实
浏览器测试修复 StrictMode 重复初始化、审批竞态和 Trace 展示问题。

## 当前限制

- Workflow 意图路由是有意设计的确定性逻辑，不会伪装成语言模型。
- 登录、部署、RAG 和多用户权限不在本次范围内。
- 第三方中转站可能较慢或超时；应用会记录经过脱敏的运行失败，不向前端暴露供应商诊断信息或凭据。
- macOS 策略是本机 MVP 防护，不是生产级安全沙箱。
- Real Agent 依赖兼容 OpenAI 风格的中转接口；Workflow 始终是所有支持平台上的便携验收路径。

## 安全

不要提交 `.env`、API Key、Token、私人账户数据或未经脱敏的录屏。本机 macOS 命令约束只是
MVP 防护，不宣称为生产级沙箱。
