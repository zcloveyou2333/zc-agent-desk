# Workflow Runtime 与关键词分析设计

## 目标

让用户无需重启应用即可在零 Key 确定性 Workflow 与 Hermes Real Agent 之间切换，并加入一个
正式命名为 `关键词分析` 的多步 Workflow。其设计保留原决策支持项目中“具名流程、显式步骤和
结构化中间结果”的有效思想，但不复制私人数据、提示词或源码。

## 产品用语与笔试兼容性

UI 使用两个名称：

- **Workflow**：由代码预编排、通过自然语言触发、不使用模型 Key；
- **Real Agent**：由 Hermes 和真实模型自主选择并执行工具。

Workflow 是笔试要求的 Mock 实现，README 必须明确这一映射。内部继续接受 `mock` 作为兼容
别名，但公开运行请求使用 `workflow` 或 `hermes`。

## Runtime 可用性与启动

`APP_MODE` 支持：

- `auto`（推荐）：始终启用 Workflow；仅在 Hermes 可执行文件和四项必要环境变量完整时启动 Real Agent；
- `mock`：只启用 Workflow，绝不启动 Hermes；
- `hermes`：要求 Real Agent 配置完整，缺失时快速失败。

健康接口返回每个 Runtime 的能力：

```json
{
  "status": "ok",
  "mode": "auto",
  "runtimes": {
    "workflow": {"available": true},
    "hermes": {"available": false, "reason": "Real Agent 尚未配置"}
  }
}
```

原因文本不得包含路径、供应商 URL 或凭据。Real Agent 不可用时返回 HTTP 503，且不持久化
用户消息或运行，不静默回退到 Workflow。

## 运行 API 与持久化

`POST /api/conversations/{id}/runs` 接受按消息选择的模式：

```json
{"message": "分析 2026-06 飘窗垫的关键词需求", "mode": "workflow"}
```

`runs.runtime_mode` 存储实际 Runtime。迁移时历史 `mock` 运行归为 `workflow`，历史 Hermes
运行保持 `hermes`。前端用 `localStorage` 保存用户偏好，并根据健康能力校验；Real Agent
不可用时自动回到 Workflow。

## Workflow 边界

- `WorkflowRegistry`：注册定义并根据自然语言选择一个流程；
- `WorkflowDefinition`：描述名称、触发条件、参数提取、有序步骤和最终渲染；
- `KeywordAnalysisWorkflow`：本版本唯一正式注册的定义；
- 现有订单、待办和上下文确定性处理器继续作为 Workflow Runtime 的后备业务流程。

## 关键词分析 Workflow

### 触发与参数

当消息包含 `关键词分析`、`关键词需求` 或“分析……关键词”时触发。提取：

- 月份：支持 `YYYY-MM`、`YYYY年M月` 和当前年份的 `M月`；
- 类目：本版本合成数据支持 `飘窗垫` 与 `办公背包`。

缺少或不支持的参数返回可执行的中文提示，不产生不完整报告。

### 有序步骤

1. `识别关键词分析 Workflow`
2. `提取月份与类目`
3. `查询合成关键词数据`
4. `分类八大需求`
5. `计算趋势与高增长词根`
6. `生成分析结果`

每个步骤使用现有 `tool.started` 和 `tool.completed` 事件，因此对话内活动卡和右侧 Trace 无需
新的前端协议。

### 合成数据与分析

数据文件只包含虚构的关键词、搜索人气、环比变化和分类标签。八类需求为品类、属性、功能、
场景、人群、风格、痛点和服务需求。分析计算各类总人气与占比，按环比识别高增长词根，并生成
简洁结论和行动建议。输出明确说明数据是合成数据，不能用于真实商业决策。

## 现有确定性行为

Workflow 继续支持普通上下文记忆、Mock 订单查询和待办审批。只有正式匹配关键词意图时才进入
`关键词分析`，避免把整个 Workflow Runtime 错误等同于一个流程。

## 错误与安全行为

- Workflow 使用本地合成数据，不读取私人项目数据或访问网络；
- Real Agent 不可用时在持久化前返回 HTTP 503；
- 真实供应商故障沿用脱敏 Hermes 失败处理；
- Runtime 选择不改变 terminal/file 的审批和路径策略；
- 失败的 Real Agent 运行不会自动切换到 Workflow，以免掩盖真实失败。

## 测试策略

- Workflow 注册、触发、参数格式、类目/月不存在和确定性计算单元测试；
- API 按运行选择、`mock` 兼容别名、不可用 Hermes 无持久化测试；
- `auto`/`mock`/`hermes` 启动契约测试；
- 前端能力类型、选择持久化、不可用回退和请求体测试；
- 浏览器验证六步 Trace、混合 Runtime 卡片、刷新恢复和 760px 布局。

## 排除范围

不实现用户自定义 Workflow 编辑器、通用 DAG 引擎、LLM 生成 Workflow 报告、真实关键词数据
接入、跨 Runtime 自动回退或把 Claude Code Unpacked 十一阶段机械映射为目录。
