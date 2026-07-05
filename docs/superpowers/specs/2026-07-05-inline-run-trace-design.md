# 对话内运行 Trace 设计

## 目标

在聊天流中展示工具调用和失败信息，形成类似 Manus 的紧凑 Agent 活动体验，同时保留右侧
Inspector 作为完整审计 Trace。用户无需在聊天和 Trace 之间来回比对，就能理解本轮运行。

## 选定交互

每条用户消息后插入一张运行活动卡，最终助手回复显示在卡片之后：

- 默认折叠，只显示运行中、等待审批、完成或失败摘要；
- 展开后显示按顺序排列的工具、脱敏参数、结果、耗时和失败详情；
- 审批仍使用独立高可见卡片，不隐藏在折叠内容中；
- 无工具运行显示“运行已完成”，避免把普通回答伪装成工具调用。

## 数据模型与 API

在 `messages` 增加可空 `run_id`，通过增量迁移兼容历史数据库。新用户消息和助手回复都写入
对应 run ID；`GET /api/conversations/{id}` 返回该关联。运行事件继续以 SQLite 为事实来源，
不新增第二套活动协议。

## 前端结构

- `runActivity.ts`：把原始事件折叠为稳定的活动 ViewModel，并负责参数脱敏和工具中文标签。
- `RunActivityCard.tsx`：渲染可访问的折叠/展开卡片。
- `ChatWorkspace.tsx`：根据 `message.run_id` 把卡片放到用户消息和助手回复之间。
- `App.tsx`：流式事件按 `(run_id, sequence)` 合并，最终再从后端刷新。
- `Inspector.tsx`：继续展示完整事件，并把失败工具和运行标红。

## 事件呈现

| 事件 | 对话内呈现 |
| --- | --- |
| `tool.started` | 新增“进行中”工具步骤。 |
| `approval.required` | 步骤进入“等待审批”，并显示审批卡。 |
| `tool.completed` | 标记完成或失败，显示脱敏结果和耗时。 |
| 连续 `message.delta` | 不逐 Token 生成步骤，只在 Inspector 折叠为“生成回复”。 |
| `run.failed` | 活动卡标红并显示脱敏失败详情。 |

工具标签包括 `query_mock_business`、`create_todo`、`terminal`、`write_file`、`patch`
和 `apply_patch`；未知工具回退显示原始名称。

## 故障行为

模型或中转站失败使用 `run.failed` 的已脱敏 `message`。工具结果中的敏感键名（Key、Token、
Secret、Authorization、Password）显示为 `[已隐藏]`，长字符串截断。UI 不根据耗时猜测
Hermes 是否重试，只展示协议中实际观察到的状态。

## 无障碍与响应式

活动卡使用真实 button、`aria-expanded` 和文字状态，不只依赖颜色。窄屏卡片取消左右缩进，
代码内容允许换行和内部滚动。

## 测试策略

- 后端迁移、消息关联、实时失败关联和历史 null 数据回归测试；
- ViewModel 对运行、完成、审批、工具失败、运行失败和脱敏的单元测试；
- 组件折叠、展开和可访问名称测试；
- App 流式合并与去重测试；
- 浏览器验证订单工具、失败显示、刷新恢复和 760px 布局。

## 排除范围

不展示 Hermes 内部思维过程，不猜测未进入 SSE 的重试，不加入独立任务面板，也不复制右侧
完整 Trace 的全部事件。
