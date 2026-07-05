# 全中文文档改造实施计划

> **面向 Agent 执行者：** 必须使用 `superpowers:executing-plans`，按任务逐项实施并在每批后检查差异。所有步骤使用复选框跟踪。

**目标：** 将 `README.md` 与 `docs/**/*.md` 的说明性内容全部翻译为中文，同时保持代码、命令、路径、API 和技术标识符不变。

**实施方式：** 按阅读优先级分三批进行人工语义翻译，每批单独检查 Markdown 结构与 Git diff。最后通过英文自然语言扫描、内部链接检查、自动化测试、构建和发布扫描共同验收。

**技术栈：** Markdown、Mermaid、ripgrep、Git、pytest、Vitest、Vite。

---

### 任务 1：翻译核心交付文档

**文件：**

- 修改：`README.md`
- 修改：`docs/PROGRESS.md`
- 修改：`docs/RECORDING.md`
- 修改：`docs/AI_COLLABORATION.md`

- [ ] **步骤 1：记录英文基线**

运行：

```bash
rg -n '^[A-Za-z][A-Za-z ,:;()/-]{20,}$' README.md docs/PROGRESS.md docs/RECORDING.md docs/AI_COLLABORATION.md
```

预期：列出需要翻译的英文标题或正文，不把代码块中的命令视为翻译目标。

- [ ] **步骤 2：逐段翻译核心材料**

保持演示命令、提示词、API、事件名和环境变量原样；将读者可见的标题、正文、表格和列表翻译为自然中文。

- [ ] **步骤 3：检查结构和差异**

运行：

```bash
git diff --check
git diff -- README.md docs/PROGRESS.md docs/RECORDING.md docs/AI_COLLABORATION.md
```

预期：无空白错误；代码块、链接目标和验证数字未被误改。

- [ ] **步骤 4：提交核心文档**

```bash
git add README.md docs/PROGRESS.md docs/RECORDING.md docs/AI_COLLABORATION.md
git commit -m "docs: translate core delivery documents"
```

### 任务 2：翻译架构与决策文档

**文件：**

- 修改：`docs/ARCHITECTURE.md`
- 修改：`docs/DESIGN.md`
- 修改：`docs/DECISIONS.md`
- 修改：`docs/IMPLEMENTATION_PLAN.md`

- [ ] **步骤 1：逐段翻译架构说明**

翻译 Mermaid 的解释性节点、生命周期表格和安全边界说明；保留组件名、状态值和事件名原样。

- [ ] **步骤 2：逐段翻译设计与决策记录**

保持历史决策的采纳、修改、拒绝结论不变，不增强 macOS 本地约束或 Hermes 集成的安全声明。

- [ ] **步骤 3：检查 Markdown 与术语**

运行：

```bash
git diff --check
rg -n 'cwd|sandbox-exec|APP_MODE|approval.required|message.delta' docs/ARCHITECTURE.md docs/DESIGN.md docs/DECISIONS.md docs/IMPLEMENTATION_PLAN.md
```

预期：技术标识符仍可检索，周围说明已改为中文。

- [ ] **步骤 4：提交架构文档**

```bash
git add docs/ARCHITECTURE.md docs/DESIGN.md docs/DECISIONS.md docs/IMPLEMENTATION_PLAN.md
git commit -m "docs: translate architecture and decisions"
```

### 任务 3：翻译历史设计规格

**文件：**

- 修改：`docs/superpowers/specs/2026-07-03-g2-frontend-design.md`
- 修改：`docs/superpowers/specs/2026-07-05-final-demo-script-design.md`
- 修改：`docs/superpowers/specs/2026-07-05-inline-run-trace-design.md`
- 修改：`docs/superpowers/specs/2026-07-05-workflow-runtime-design.md`

- [ ] **步骤 1：翻译规格的目标、边界和验收条件**

保留接口载荷、类型名、CSS 类名、工具名及示例提示词原样，翻译其上下文说明。

- [ ] **步骤 2：检查规格内部一致性**

运行：

```bash
rg -n 'TBD|TODO|PLACEHOLDER|待定' docs/superpowers/specs
git diff --check
```

预期：没有占位内容或空白错误。

- [ ] **步骤 3：提交规格翻译**

```bash
git add docs/superpowers/specs
git commit -m "docs: translate design specifications"
```

### 任务 4：翻译历史实施计划

**文件：**

- 修改：`docs/superpowers/plans/2026-07-03-g2-frontend.md`
- 修改：`docs/superpowers/plans/2026-07-03-g3-hermes-integration.md`
- 修改：`docs/superpowers/plans/2026-07-05-inline-run-trace.md`
- 修改：`docs/superpowers/plans/2026-07-05-workflow-runtime.md`

- [ ] **步骤 1：翻译任务、步骤和预期结果**

保留代码块、测试代码、命令和 commit message 原样，翻译标题、文件说明、步骤文字以及 `Expected` 后的自然语言解释。

- [ ] **步骤 2：检查计划可执行性**

运行：

```bash
rg -n '^```|^### |^- \[[ x]\]' docs/superpowers/plans
git diff --check
```

预期：代码围栏成对、任务和复选框仍存在、无空白错误。

- [ ] **步骤 3：提交计划翻译**

```bash
git add docs/superpowers/plans
git commit -m "docs: translate implementation plans"
```

### 任务 5：全仓库文档验收

**文件：**

- 检查：`README.md`
- 检查：`docs/**/*.md`

- [ ] **步骤 1：扫描残留英文自然语言**

运行：

```bash
rg -n '^[A-Za-z][A-Za-z ,:;()''"/.-]{20,}$' README.md docs
```

逐条判断：代码、命令、路径、API、专有名词可保留；完整英文标题或说明必须翻译。

- [ ] **步骤 2：验证内部 Markdown 链接**

使用脚本提取相对 `.md` 链接并确认目标文件存在；外部 HTTP 链接不做本地存在性检查。

- [ ] **步骤 3：运行完整项目验证**

```bash
.venv/bin/pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run build
.venv/bin/python scripts/release_check.py
git diff --check
```

预期：后端和前端测试全部通过，生产构建和发布扫描成功，Git 无空白错误。

- [ ] **步骤 4：核对最终提交范围**

```bash
git status --short --branch
git log --oneline --decorate -8
```

预期：工作区干净，新增提交只涉及 Markdown 文档。
