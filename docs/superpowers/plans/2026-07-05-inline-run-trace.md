# 对话内运行 Trace 实施计划

> **执行要求：** 使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development`，以测试驱动方式逐项实施。

**目标：** 在每条用户消息后展示可展开运行卡，实时呈现工具活动和失败，同时保留右侧完整 Agent Trace。

**架构：** 通过 `messages.run_id` 建立显式消息与运行关联；纯函数把事件折叠为活动 ViewModel；
React 在聊天流中插入卡片，并按 `(run_id, sequence)` 合并 SSE。

**技术栈：** FastAPI、SQLite、React、TypeScript、Vitest、Testing Library。

---

## 文件映射

- 后端：`backend/zc_agent_desk/app.py`
- 前端模型：`frontend/src/runActivity.ts`
- 前端组件：`frontend/src/components/RunActivityCard.tsx`
- 集成：`frontend/src/App.tsx`、`ChatWorkspace.tsx`、`Inspector.tsx`
- 测试：`tests/g2/test_mock_api.py`、`tests/g3/test_live_runtime.py`、前端对应 `*.test.tsx`

### 任务 1：持久化消息与运行的显式关联

- [ ] 先写迁移失败测试，证明历史消息允许 `run_id=null`。
- [ ] 新用户消息和助手消息写入同一个 run ID。
- [ ] 会话详情返回 `run_id`，更新前端 `Message` 类型。
- [ ] 运行：`.venv/bin/pytest -q tests/g2/test_mock_api.py tests/g3/test_live_runtime.py`
- [ ] 提交：`git commit -m "feat: correlate messages with agent runs"`

### 任务 2：构建运行活动 ViewModel

- [ ] 测试运行中、完成、审批、工具失败、运行失败和无工具运行。
- [ ] 实现工具中文标签、参数敏感键隐藏、长文本截断和耗时计算。
- [ ] 连续 `message.delta` 不生成多条工具步骤。
- [ ] 运行：`npm --prefix frontend test -- --run src/runActivity.test.ts`
- [ ] 提交：`git commit -m "feat: summarize agent run activity"`

### 任务 3：渲染可访问的对话内活动卡

- [ ] 先写组件失败测试，覆盖摘要、`aria-expanded`、展开步骤、结果和失败详情。
- [ ] 使用真实 button 和文字状态实现 `RunActivityCard`。
- [ ] 在用户消息与对应助手回复之间插入卡片；审批卡保持独立。
- [ ] 补充响应式样式和代码内容内部滚动。
- [ ] 提交：`git commit -m "feat: show tool activity inside chat"`

### 任务 4：合并实时事件并增强失败 Trace

- [ ] App 测试模拟流未结束时到达 `tool.started`，确认卡片立即出现。
- [ ] 按 run ID 和 sequence 合并事件，忽略重放重复项。
- [ ] Inspector 把失败工具/运行标红，并提供脱敏详情。
- [ ] 运行完整前端测试与构建。
- [ ] 提交：`git commit -m "feat: stream failures into agent trace"`

### 任务 5：文档、浏览器与发布验证

- [ ] 更新架构、决策、AI 协作和进度，明确不猜测 Hermes 内部重试。
- [ ] 浏览器验证订单工具、卡片展开、失败、刷新恢复和 760px 视口。
- [ ] 运行后端、前端、构建和发布扫描。
- [ ] 提交：`git commit -m "docs: record inline trace verification"`
