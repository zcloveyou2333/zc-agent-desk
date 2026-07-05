import { formatArguments, summarizeRun, toolLabel } from './runActivity';
import type { Run } from './types';

function run(overrides: Partial<Run> = {}): Run {
  return {
    id: 'r1',
    conversation_id: 'c1',
    status: 'completed',
    runtime_mode: 'workflow',
    pending_tool: null,
    pending_args: null,
    events: [],
    ...overrides,
  };
}

it('summarizes a successful tool call with duration', () => {
  const activity = summarizeRun(run({
    events: [
      { run_id: 'r1', sequence: 1, type: 'tool.started', data: { tool: 'query_mock_business', arguments: { order_id: 'ORD-1001' } }, created_at: '2026-07-05T10:00:00Z' },
      { run_id: 'r1', sequence: 2, type: 'tool.completed', data: { tool: 'query_mock_business', duration: 0.013, error: false }, created_at: '2026-07-05T10:00:01Z' },
    ],
  }));

  expect(activity).toMatchObject({ tone: 'success', title: '已完成 1 个工具调用', duration: '0.01 秒' });
  expect(activity.steps).toEqual([
    expect.objectContaining({ label: '查询业务订单', state: 'completed', arguments: { order_id: 'ORD-1001' } }),
  ]);
});

it('summarizes running and failed activity', () => {
  const running = summarizeRun(run({
    status: 'running',
    events: [{ run_id: 'r1', sequence: 1, type: 'tool.started', data: { tool: 'create_todo' }, created_at: '2026-07-05T10:00:00Z' }],
  }));
  const failed = summarizeRun(run({
    status: 'failed',
    events: [
      { run_id: 'r1', sequence: 1, type: 'tool.started', data: { tool: 'query_mock_business' }, created_at: '2026-07-05T10:00:00Z' },
      { run_id: 'r1', sequence: 2, type: 'tool.completed', data: { tool: 'query_mock_business', error: true }, created_at: '2026-07-05T10:00:01Z' },
      { run_id: 'r1', sequence: 3, type: 'run.failed', data: { message: 'Hermes run failed' }, created_at: '2026-07-05T10:00:02Z' },
    ],
  }));

  expect(running).toMatchObject({ tone: 'running', title: '正在调用 创建待办…' });
  expect(failed).toMatchObject({ tone: 'failed', title: '模型请求失败', detail: 'Hermes run failed' });
  expect(failed.steps[0]).toMatchObject({ label: '查询业务订单', state: 'failed' });
});

it('redacts sensitive values, truncates text, and keeps unknown tool names', () => {
  expect(formatArguments({ api_token: 'secret', password: '123', order_id: 'ORD-1001', note: 'x'.repeat(200) })).toEqual({
    api_token: '[已隐藏]',
    password: '[已隐藏]',
    order_id: 'ORD-1001',
    note: `${'x'.repeat(157)}…`,
  });
  expect(toolLabel('custom_lookup')).toBe('custom_lookup');
});
