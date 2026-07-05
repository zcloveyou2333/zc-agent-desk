import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RunActivityCard from './RunActivityCard';
import type { Run } from '../types';

const completedRun: Run = {
  id: 'r1',
  conversation_id: 'c1',
  status: 'completed',
  runtime_mode: 'workflow',
  pending_tool: null,
  pending_args: null,
  events: [
    { run_id: 'r1', sequence: 1, type: 'tool.started', data: { tool: 'query_mock_business', arguments: { order_id: 'ORD-1001', api_token: 'hidden' } }, created_at: '2026-07-05T10:00:00Z' },
    { run_id: 'r1', sequence: 2, type: 'tool.completed', data: { tool: 'query_mock_business', duration: 0.013, error: false }, created_at: '2026-07-05T10:00:01Z' },
  ],
};

it('shows a compact summary and expands sanitized tool details', async () => {
  const user = userEvent.setup();
  render(<RunActivityCard run={completedRun} />);

  const toggle = screen.getByRole('button', { name: /已完成 1 个工具调用/ });
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(screen.queryByText('查询业务订单')).not.toBeInTheDocument();

  await user.click(toggle);

  expect(toggle).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByText('查询业务订单')).toBeInTheDocument();
  expect(screen.getByText(/ORD-1001/)).toBeInTheDocument();
  expect(screen.getByText(/\[已隐藏\]/)).toBeInTheDocument();
});

it('exposes a failed run as an alert', () => {
  render(<RunActivityCard run={{
    ...completedRun,
    status: 'failed',
    events: [{ run_id: 'r1', sequence: 1, type: 'run.failed', data: { message: 'Hermes run failed' }, created_at: '2026-07-05T10:00:00Z' }],
  }} />);

  expect(screen.getByRole('alert')).toHaveTextContent('模型请求失败');
});
