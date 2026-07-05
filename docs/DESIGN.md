# ZC Agent Desk 设计说明

## 目标

交付一个内部员工 Chatbot，展示多轮对话、模型自主选择工具、写操作的真实审批边界、零 Key
Mock 模式，以及可选的 Hermes Runtime。

产品名称为 **ZC Agent Desk**，署名为 **由 zcloveyou 构建**。

## Runtime 边界

- React 负责输入、渲染、审批控件和 Trace 查看器。
- FastAPI 负责公开 API、会话、持久化、运行状态、Mock 行为和 Runtime 事件标准化。
- Hermes 作为 sidecar 运行，负责实时模型与工具循环。
- 项目级 Hermes 插件提供 `query_mock_business` 和 `create_todo`，不修改 Hermes 核心。
- SQLite 存储会话、消息、运行、事件、审批、待办和确定性 Mock 订单。

Input -> Message -> History -> System -> API -> Tokens -> Tools -> Loop ->
Render -> Hooks -> Await 是解释生命周期和 Trace 的模型，不代表十一个源码目录。

## 模式

`APP_MODE=mock` 不需要 API Key 或 Hermes 安装，并且必须覆盖与实时模式相同的公开运行、
事件、工具和审批协议。

`APP_MODE=hermes` 把运行发送到固定版本的 Hermes sidecar；后者连接支持结构化工具调用的
OpenAI-compatible Chat Completions 接口。模型标识通过 `MODEL_NAME` 提供，与本地既有
项目约定一致。

## 工具

- `query_mock_business(order_id)` 是只读操作，会自动执行。
- `create_todo(title, due_at?, priority?)` 在持久化前暂停。批准只创建一个待办；拒绝、超时
  或重放不创建待办。
- Hermes 开发者工具只在 macOS 上开放终端和文件操作，命令与修改均需审批。操作系统策略是
  本机防护，不是生产级跨平台沙箱。

## 运行状态

运行依次进入 `queued`、`running`、`awaiting_approval`，最后进入 `completed`、
`failed` 或 `cancelled`。批准、拒绝和取消均为幂等。

公开事件包括 `message.delta`、`tool.started`、`approval.required`、`tool.completed`、
`message.completed` 和 `run.failed`。事件使用单调递增序号，SSE 客户端可从最后看到的事件重连。

## 有意排除的范围

MVP 不包含登录认证、线上部署、检索增强生成、多用户权限或复杂多工具规划。
