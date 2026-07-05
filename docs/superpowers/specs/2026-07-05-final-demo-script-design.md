# Final Demo Script Design

## Goal

Produce a roughly ten-minute Chinese screen recording that demonstrates both
the stable zero-key Workflow path and a live Hermes-backed Real Agent path. The
recording should emphasize engineering judgment, observable execution, and a
runnable delivery rather than enumerate every feature.

## Narrative

The recording follows one argument: ZC Agent Desk supports the same persisted
conversation and Trace contract across two honest runtime choices.

1. Workflow provides deterministic, zero-key business automation.
2. Real Agent lets a model select tools while application approvals control
   side effects.
3. Shared persistence, normalized events, tests, and explicit limitations make
   both paths reviewable.

## Timeline

| Time | Screen | Purpose |
| --- | --- | --- |
| 0:00–1:00 | Application and README | State the employee-chatbot problem, deliverable, and excluded scope. |
| 1:00–2:00 | Architecture document | Explain React, FastAPI, SQLite, runtime selection, Hermes sidecar, and normalized events. |
| 2:00–4:00 | Workflow UI | Run `分析 2026年6月飘窗垫的关键词需求`, expand all six steps, and explain synthetic data and zero-key operation. |
| 4:00–6:30 | Real Agent UI | Switch without restarting, query `ORD-1001`, create one todo, and approve the blocked write. |
| 6:30–8:00 | Inline cards and Agent Trace | Show tool details, failure visibility, persistence, and the distinction between concise chat activity and complete audit Trace. |
| 8:00–9:15 | AI collaboration record | Explain three rejected or modified suggestions: no Hermes rewrite, no fake model-like Mock, and no `cwd`-as-sandbox claim. |
| 9:15–10:00 | Verification output and limitations | Show tests, build, release scan, pinned Hermes revision, relay risk, and local sandbox limitations. |

## Live Prompts

- Workflow: `分析 2026年6月飘窗垫的关键词需求`
- Real read: `请查询订单 ORD-1001，并告诉我状态`
- Real write: `请直接使用 create_todo 工具创建待办：检查最终录屏。不要调用其他工具。`

The presenter waits for each final response before starting the next prompt and
expands only one representative activity card to keep the recording moving.

## Failure Handling

If the relay is slow, wait briefly while explaining that Real Agent is an
external dependency. If it reaches an explicit failure, show the persisted red
failure card and Agent Trace, state that the zero-key Workflow remains usable,
and continue to verification evidence. Do not retry repeatedly or imply that a
failed live run succeeded.

## Privacy and Presentation

- Never show `.env`, provider URLs, API dashboards, terminal history, browser
  bookmarks, notifications, or account details.
- Prepare one clean conversation and clear irrelevant demo history before
  recording.
- Keep the terminal limited to known verification commands and their final
  summaries.
- Perform a full-speed review and a frame-by-frame privacy review before
  sharing the video.

## Deliverable

The final script will be added to `docs/FINAL_DEMO_SCRIPT.md`. Each segment will
contain: target time, screen action, natural Chinese narration, and a concise
fallback line where live behavior can vary.
