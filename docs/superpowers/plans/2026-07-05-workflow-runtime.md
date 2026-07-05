# Workflow Runtime 实施计划

> **执行要求：** 使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development`，按测试驱动步骤执行。

**目标：** 在一个应用中运行零 Key `关键词分析` Workflow 与 Hermes Real Agent，通过 UI 按消息切换，无需重启。

**架构：** FastAPI 为每个 run 存储 `runtime_mode` 并分发到本地 Workflow Registry 或 Hermes Adapter。
`APP_MODE=auto` 根据配置决定是否启动 sidecar；React 使用健康能力控制 Runtime Switch。

**技术栈：** FastAPI、SQLite、React、TypeScript、Shell、pytest、Vitest。

---

## 文件映射

- Workflow：`backend/zc_agent_desk/workflows/`
- Runtime API：`backend/zc_agent_desk/app.py`
- 启动：`scripts/dev.sh`、`scripts/runtime_mode.sh`、`.env.example`
- 前端：`frontend/src/types.ts`、`api.ts`、`App.tsx`、`RuntimeSwitch.tsx`
- 文档：README、架构、进度、AI 协作和录屏清单

### 任务 1：实现确定性关键词分析核心

- [ ] 先测试注册表匹配、月份格式、支持类目、缺失参数和确定性结果。
- [ ] 定义 `WorkflowStep`、`WorkflowResult` 和 Workflow Protocol。
- [ ] 创建只含虚构记录的 `synthetic_keywords.json`。
- [ ] 实现八大需求汇总、占比、高增长词根和中文报告。
- [ ] 运行：`.venv/bin/pytest -q tests/workflows/test_keyword_analysis.py`
- [ ] 提交：`git commit -m "feat: add keyword analysis workflow"`

### 任务 2：增加按运行持久化与 API 选择

- [ ] 测试 Workflow 六步事件、Hermes 分发、`mock` 别名和不可用 Hermes 无持久化。
- [ ] 为 `runs` 增量增加 `runtime_mode`，历史值安全迁移。
- [ ] `RunCreate.mode` 接受 `workflow`、`mock`、`hermes`；存储时把 `mock` 归一为 `workflow`。
- [ ] 健康接口返回两个 Runtime 的 `available` 与可选 `reason`。
- [ ] 运行 Runtime、Mock 和 Live 测试后提交。

### 任务 3：一次启动支持 Workflow 与 Real Agent

- [ ] Shell 契约测试覆盖 `auto` 配置完整/缺失、`mock` 和 `hermes`。
- [ ] `runtime_mode.sh` 只检查变量是否存在，不输出值。
- [ ] `dev.sh` 始终启动 Workflow，并在 `HERMES_ENABLED=1` 时启动 sidecar。
- [ ] `.env.example` 默认使用 `APP_MODE=auto`。
- [ ] 执行 `bash -n scripts/dev.sh scripts/runtime_mode.sh` 后提交。

### 任务 4：扩展前端 API 与 Runtime 类型

- [ ] 定义 `RuntimeMode`、`RuntimeCapability`，并为 `Run` 增加 `runtime_mode`。
- [ ] `createRun` 请求体发送 `{message, mode}`。
- [ ] 更新 API 测试与所有固定数据，生产构建必须通过。
- [ ] 提交：`git commit -m "feat: send runtime with each run"`

### 任务 5：加入 Workflow / Real Agent Switch

- [ ] 组件测试覆盖 `aria-pressed`、模式回调、Real Agent 禁用和原因文本。
- [ ] App 测试覆盖选择持久化、请求模式和不可用回退。
- [ ] 输入框上方渲染分段按钮；左栏按能力显示 `Workflow + Real` 或 `Workflow Runtime`。
- [ ] 运行卡根据自身 `runtime_mode` 显示 Runtime，而不是当前全局选择。
- [ ] 修复长会话桌面布局，使三栏在视口内独立滚动。
- [ ] 提交：`git commit -m "feat: switch workflow and real agent per message"`

### 任务 6：文档与发布验证

- [ ] README 明确 Workflow 是笔试 Mock 实现，记录关键词提示词和三种启动模式。
- [ ] 更新架构、AI 协作、进度和录屏材料。
- [ ] 在 `auto` 模式浏览器验证六步 Workflow、刷新恢复、Real Agent 切换和 760px 布局。
- [ ] 完整运行：

```bash
.venv/bin/pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run build
./scripts/setup_hermes.sh --verify-only
.venv/bin/python scripts/release_check.py
```

- [ ] 提交：`git commit -m "docs: complete workflow runtime delivery"`
