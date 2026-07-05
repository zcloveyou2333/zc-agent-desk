# 决策记录

## 2026-07-03

### 复用 Hermes，不重构其核心

Hermes 是成熟且快速变化的 Runtime，核心会话循环远大于本次笔试范围。ZC Agent Desk 通过
版本化 HTTP Adapter 和项目插件集成，而不是把上游源码重组为十一个解释性生命周期阶段。

### 保持 Mock 模式独立

笔试要求核心流程在没有真实模型 Key 时也能运行。Mock Runtime 使用确定性逻辑和相同应用
协议，并保持测试离线。实时 Hermes 是单独验证的集成路径。

### 副作用执行前必须审批

业务读取自动执行。创建待办、终端命令和文件修改必须等待显式决策。拒绝或重放审批不得产生副作用。

### 如实描述本机执行约束

设置工作目录不能限制 Shell。只有操作系统策略探针通过后，macOS 才开放开发者工具；其他平台
禁用这些工具，但保留业务 Chatbot。

### 隔离 Hermes 配置

插件发现需要 `HERMES_ENABLE_PROJECT_PLUGINS=1`，启用还需要单独配置 `plugins.enabled`。
ZC Agent Desk 使用项目内独立的 `HERMES_HOME` 和配置模板，安装过程不会修改开发者个人
`~/.hermes` 配置。

### 统一使用 `MODEL_NAME`

实时供应商模型通过 `MODEL_NAME` 配置，与开发者既有项目保持一致。不再接受第二个别名
`OPENAI_MODEL`，避免中断恢复和安装说明产生歧义。

### 固定已验证的上游 commit 和关键哈希

手动下载的 Hermes 0.18.0 压缩包已匹配上游 commit
`5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37`。项目记录该不可变 commit，并保存包清单、
API Server 和插件加载器的 SHA-256。安装前会验证三项哈希。

### 将中转凭据绑定到具名自定义供应商

Hermes 0.18 为保护凭据，不会把裸自定义供应商中的通用 `OPENAI_API_KEY` 转发给非 OpenAI
主机。ZC Agent Desk 使用具名供应商 `custom:zc-relay` 和 `key_env: OPENAI_API_KEY`，
既让接收方明确，又只在环境变量中保存密钥。

### 使用 Hermes manual 审批模式

Hermes 0.18 支持 `manual`、`smart` 和 `off`；`ask` 无效，只会伴随警告回退到 `manual`。
固定模板使用 `manual`，实时危险命令探针验证了请求、拒绝和运行恢复。

### Mock 路由保持确定性和显式

Mock 模式不调用模型，通过显式规则识别笔试演示意图。这样既诚实表达零 Key 行为，也让订单、
审批、拒绝、重放和取消测试可以重复。只有实时模式由 Hermes 负责模型自主路由。

### 使用浅色企业控制台界面

项目比较了三种视觉方向，最终选择浅蓝灰控制台，因为在 8–12 分钟录屏中，HR 和工程评审者都能
清楚阅读业务流程、审批状态和 Agent Trace。桌面使用三栏；窄屏优先保留聊天并堆叠 Inspector。

### 保留 React StrictMode，并保护初始化

浏览器验收发现异步空状态初始化在 StrictMode 开发探针下创建两个会话。项目保留 StrictMode；
同步 ref 保护使启动副作用只运行一次，回归测试验证该行为。

### 使用应用 run ID 关联插件调用

FastAPI 把本地 run ID 作为 Hermes `session_id`。Hermes 将该值转发给项目工具处理器和 Hook，
带认证桥接因此可以把审批提案关联到正确的持久化运行，无需修改 Hermes 或暴露第二个公开关联 API。

### 开发者工具审批由项目策略负责

Hermes manual 审批只覆盖它判定为危险的命令。笔试要求每次 terminal、write 和 patch 都暂停，
因此项目 `pre_tool_call` Hook 会检查路径并阻塞等待应用审批。原生审批设为 `off`，避免重复提示；
macOS 操作系统策略仍是独立约束层。

### 未找到订单属于业务结果

未知订单时，内部桥接以 HTTP 200 返回 `{found: false}`。HTTP 错误只表示认证或基础设施故障，
让模型可以区分“订单不存在”和“后端不可用”。

### 在可视化 Trace 中折叠 Token delta

所有 delta 仍可持久化和重放，但连续 `message.delta` 在界面中渲染为一条“生成回复”生命周期记录。
这样既保留协议证据，又避免短回复产生几十条视觉相同记录。
