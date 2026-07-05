import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Inspector from './Inspector';
import type { RunEvent } from '../types';

it('marks failed tools and runs and reveals sanitized detail', async () => {
  const user = userEvent.setup();
  const events: RunEvent[] = [
    { run_id: 'r1', sequence: 1, type: 'tool.completed', data: { tool: 'query_mock_business', error: true }, created_at: '2026-07-05T10:00:00Z' },
    { run_id: 'r1', sequence: 2, type: 'run.failed', data: { message: 'Hermes run failed' }, created_at: '2026-07-05T10:00:01Z' },
  ];

  render(<Inspector events={events} todos={[]} />);

  expect(screen.getByText('工具执行失败')).toBeInTheDocument();
  expect(screen.getByText('运行失败')).toBeInTheDocument();
  expect(screen.getByText(/查询业务订单/)).toBeInTheDocument();
  await user.click(screen.getByText('查看失败详情'));
  expect(screen.getByText('Hermes run failed')).toBeVisible();
});
