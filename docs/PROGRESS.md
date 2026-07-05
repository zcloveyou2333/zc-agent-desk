# 进度与恢复说明

## 当前 Gate

G5——公开仓库已发布；Workflow Runtime 和按消息选择 Real Agent 的功能已完成最终验证并合入 `main`。

## 已完成

- 范围和架构已审批。
- 产品名确定为 ZC Agent Desk，作者标识为 zcloveyou。
- 已建立设计、决策、AI 协作格式和恢复记录。
- 两个业务工具 Schema 的项目插件契约测试通过。
- 已在隔离的 `HERMES_HOME` 中验证 Hermes 项目插件发现机制。
- macOS `sandbox-exec` 探针允许工作区写入，拒绝写入 `/tmp`，并拒绝读取 `~/.ssh`。
- 已通过 Hermes `/v1/runs` 验证实时中转文本、显式会话历史、结构化工具调用、SSE 和阻塞审批拒绝。
- FastAPI 与 SQLite 会持久化会话、消息、运行、有序事件、审批、待办和 Mock 订单。
- 确定性 Mock Runtime 支持普通上下文、订单存在/不存在、待办批准/拒绝、幂等重放、取消，以及从 `Last-Event-ID` 恢复 SSE。
- React 企业控制台采用三栏桌面布局，支持对话内审批、Trace 和待办，并在 900px 以下响应式堆叠。
- FastAPI 异步启动 Hermes 运行，把统一 SSE 事件写入 SQLite，持久化最终回复并转发取消请求。
- 带认证的项目插件读取 Mock 订单，并通过应用审批阻塞 todo、terminal、write 和 patch，不修改 Hermes 核心。
- Hermes 固定到上游 commit `5445e42b`；全新安装脚本会先验证关键哈希，再创建隔离环境。
- 公开文档覆盖架构、AI 决策、启动、限制、发布检查和 8–12 分钟录屏计划。
- Git 历史使用已批准的公开作者身份；`main` 已发布到 `zcloveyou2333/zc-agent-desk`，不含本机密钥或运行数据。
- `关键词分析` 是基于合成关键词数据的六步确定性 Workflow，包含八大需求分类和可观察中间事件。
- React 输入框可按消息选择 Workflow 或 Real Agent，持久化偏好，在 Real Agent 不可用时显示原因并禁用，同时按实际 Runtime 标记运行卡。
- `APP_MODE=auto` 始终启动 Workflow，并在可执行文件和环境变量完整时加入 Hermes；`mock` 和 `hermes` 仍可作为显式运行覆盖。
- `auto` 模式浏览器验收完成 `2026-06 飘窗垫` 合成分析，展示六个有序步骤，刷新后恢复结果，持久化 Real Agent 选择，并在 760px 视口无横向溢出。
- 验收还发现了长会话列表导致的桌面布局问题。三栏现在固定在视口内独立滚动，1280×720 下输入框保持可见；移动端仍使用页面滚动。

## G1 证据与阻塞项

- 候选版本来自手动下载的 GitHub 源码压缩包：Hermes `0.18.0`。压缩包没有 Git 元数据，因此先在 `config/hermes-source.lock` 记录三个关键文件哈希，随后又匹配并固定到上游 commit。
- Hermes 同时需要 `HERMES_ENABLE_PROJECT_PLUGINS=1` 和显式 `plugins.enabled`。配置模板记录了两项要求。
- Hermes 0.18.0 的本机 API 服务还要求 `API_SERVER_KEY`；项目级 `HERMES_API_KEY` 会映射到该原生变量。
- 在 macOS 策略下，`/health`、`/v1/models` 和 `/v1/capabilities` 均返回 HTTP 200。文本运行流式返回 `连接成功`，显式历史正确找回测试代码 `雁七`。
- Hermes 有意拒绝把通用 `OPENAI_API_KEY` 转发给裸第三方自定义域名。配置改为 `custom:zc-relay` 并绑定 `key_env: OPENAI_API_KEY`；配置文件不存储凭据。
- 模型自主调用 `query_mock_business`；Hermes 依次发出 `tool.started`、`tool.completed`、消息 delta 和终止事件，并把预期的 G1 后端占位错误返回模型。
- 无害危险命令探针发出 `approval.request`。提交 `deny` 后产生 `approval.responded`，命令未执行，工具以错误结束，模型仍生成最终回复。
- Hermes 0.18 支持 `manual`、`smart` 和 `off`，不支持旧概念值 `ask`；模板已显式使用经过实时拒绝流程验证的 `manual`。

## G2 证据

- 最终组合验证前，后端 G1+G2 测试共 18 项通过。
- 前端 API、组件、StrictMode 回归和 SSE 重放共 7 项测试通过；Vite 生产构建完成。
- 真实浏览器验收验证了 `ORD-1001`、需要审批的待办、恰好一次持久化、完整 Trace、刷新恢复和 760px 视口。
- StrictMode 探针发现首次会话被重复创建；回归测试使用 StrictMode 包裹应用，初始化保护避免重复副作用。

## G3 证据

- 真实 Hermes UI 订单查询由模型自主调用 `query_mock_business`，并返回 `ORD-1001` 已发货。
- 真实 `create_todo` 在 UI 中暂停，批准后只持久化一次，把结果返回 Hermes，再生成最终回复。
- 真实 `terminal pwd` 显示命令级审批；拒绝后未执行，最终回复说明工具被拒绝。
- 浏览器验收发现并修复实时模式标签、delta Trace 过量、审批卡刷新死锁、通用审批措辞和延迟提案取消竞态。
- 实时验证期间中转站偶发请求超时，重试后完成；该问题明确记录为上游限制。

## G4 证据

- 在不含 `.env`、`.vendor`、虚拟环境或 Node modules 的全新本机 `git clone` 中，README 安装命令执行成功。
- 该 clone 通过 39 项后端测试、8 项前端测试、Vite 生产构建、63 文件发布扫描和实际 Mock API/UI 启动。
- 首次全新安装暴露 setuptools 包发现歧义；失败回归测试推动项目把包发现明确为 `backend/zc_agent_desk`。
- 第二个全新 clone 下载不可变 Hermes commit `5445e42b`，验证三个锁定哈希，安装 Hermes 0.18.0，并报告预期上游版本。
- 发布扫描会拒绝 macOS 用户路径、形似 Key 的字符串、缺失交付文档和可变 Hermes 源码引用。

## 下一步

录制 8–12 分钟最终演示，完成逐帧隐私检查，然后向 HR 提交仓库和视频链接。

## 对话内运行 Trace 证据

- 增量迁移把新用户消息和助手消息关联到运行；历史消息的关联允许为 null。
- 会话卡展示运行中、已完成、等待审批、工具失败和运行失败状态，并可展开查看脱敏参数和结果。
- 进入的 SSE 事件先按 `(run_id, sequence)` 合并，再进行最终刷新，因此运行期间可显示工具活动，重放时不会重复。
- Agent Trace 用红色标记失败工具和运行，并显示脱敏失败详情。Hermes 内部重试日志仍不在范围内，除非 sidecar 将其纳入事件协议。
- 真实 Mock 浏览器验收验证了订单查询、展开详情、刷新恢复和 760px 响应式视口。

## 恢复协议

1. 阅读 `docs/PROGRESS.md` 和 `docs/DECISIONS.md`。
2. 执行 `git status --short --branch` 并检查最新 commit。
3. 执行当前 Gate 记录的验证命令。
4. 只有工作区验证通过后才继续当前 Gate，不提前开始后续工作。
