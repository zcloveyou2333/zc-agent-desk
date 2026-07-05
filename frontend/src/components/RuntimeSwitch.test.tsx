import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RuntimeSwitch from './RuntimeSwitch';

it('selects workflow or real agent with accessible pressed state', async () => {
  const user = userEvent.setup();
  const onChange = vi.fn();
  render(<RuntimeSwitch value="workflow" hermes={{ available: true }} onChange={onChange} />);

  expect(screen.getByRole('button', { name: 'Workflow' })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByRole('button', { name: 'Real Agent' })).toHaveAttribute('aria-pressed', 'false');
  await user.click(screen.getByRole('button', { name: 'Real Agent' }));
  expect(onChange).toHaveBeenCalledWith('hermes');
});

it('disables real agent and explains why it is unavailable', () => {
  render(<RuntimeSwitch
    value="workflow"
    hermes={{ available: false, reason: 'Real Agent 尚未配置' }}
    onChange={vi.fn()}
  />);

  expect(screen.getByRole('button', { name: 'Real Agent' })).toBeDisabled();
  expect(screen.getByText('Real Agent 尚未配置')).toBeInTheDocument();
});
