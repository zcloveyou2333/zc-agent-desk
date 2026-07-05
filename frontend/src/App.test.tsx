import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StrictMode } from 'react';
import App from './App';
import * as api from './api';
import type { ConversationDetail } from './types';

vi.mock('./api');

const detail: ConversationDetail = {
  id: 'c1',
  title: '订单与待办',
  created_at: '2026-07-03T10:00:00Z',
  messages: [
    { id: 'm1', role: 'user', content: '查询订单 ORD-1001', run_id: 'r1', created_at: '2026-07-03T10:00:00Z' },
    { id: 'm2', role: 'assistant', content: '订单 ORD-1001 当前状态：已发货。', run_id: 'r1', created_at: '2026-07-03T10:00:01Z' },
  ],
  runs: [
    {
      id: 'r1',
      conversation_id: 'c1',
      status: 'completed',
      runtime_mode: 'hermes',
      pending_tool: null,
      pending_args: null,
      events: [
        { run_id: 'r1', sequence: 1, type: 'tool.started', data: { tool: 'query_mock_business' }, created_at: '2026-07-03T10:00:00Z' },
        { run_id: 'r1', sequence: 2, type: 'tool.completed', data: { tool: 'query_mock_business' }, created_at: '2026-07-03T10:00:01Z' },
        { run_id: 'r1', sequence: 3, type: 'message.delta', data: { delta: '已' }, created_at: '2026-07-03T10:00:01Z' },
        { run_id: 'r1', sequence: 4, type: 'message.delta', data: { delta: '发货' }, created_at: '2026-07-03T10:00:01Z' },
      ],
    },
    {
      id: 'r2',
      conversation_id: 'c1',
      status: 'awaiting_approval',
      runtime_mode: 'hermes',
      pending_tool: 'create_todo',
      pending_args: { title: '周五提交周报', priority: 'normal' },
      events: [
        { run_id: 'r2', sequence: 1, type: 'approval.required', data: { tool: 'create_todo' }, created_at: '2026-07-03T10:01:00Z' },
      ],
    },
    {
      id: 'r-terminal',
      conversation_id: 'c1',
      status: 'awaiting_approval',
      runtime_mode: 'hermes',
      pending_tool: 'terminal',
      pending_args: { command: 'pwd' },
      events: [],
    },
  ],
};

beforeEach(() => {
  localStorage.clear();
  vi.mocked(api.listConversations).mockResolvedValue([{ id: 'c1', title: '订单与待办', created_at: detail.created_at }]);
  vi.mocked(api.getHealth).mockResolvedValue({
    status: 'ok',
    mode: 'auto',
    runtimes: { workflow: { available: true }, hermes: { available: true } },
  });
  vi.mocked(api.getConversation).mockResolvedValue(detail);
  vi.mocked(api.listTodos).mockResolvedValue([
    { id: 't1', title: '完成录屏', due_at: null, priority: 'normal', created_at: detail.created_at },
  ]);
  vi.mocked(api.createRun).mockResolvedValue({ run_id: 'r3', status: 'completed' });
  vi.mocked(api.streamRunEvents).mockResolvedValue(4);
  vi.mocked(api.decideApproval).mockResolvedValue({ run_id: 'r2', status: 'completed', replayed: false });
});

it('renders persisted chat, trace, pending approval, and todos', async () => {
  render(<App />);

  expect(await screen.findByText('ZC Agent Desk')).toBeInTheDocument();
  expect(screen.getByText('Workflow + Real')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Workflow' })).toHaveAttribute('aria-pressed', 'true');
  expect(await screen.findByText('订单 ORD-1001 当前状态：已发货。')).toBeInTheDocument();
  expect(screen.getAllByText('等待审批')).toHaveLength(3);
  expect(screen.getByText('周五提交周报')).toBeInTheDocument();
  expect(screen.getByText('执行终端命令')).toBeInTheDocument();
  expect(screen.getByText('pwd')).toBeInTheDocument();
  expect(screen.getByText('完成录屏')).toBeInTheDocument();
  expect(screen.getByText('工具开始')).toBeInTheDocument();
  expect(screen.getAllByText('生成回复')).toHaveLength(1);
  const userMessage = screen.getByText('查询订单 ORD-1001');
  const activity = screen.getByRole('button', { name: /已完成 1 个工具调用/ });
  const assistantMessage = screen.getByText('订单 ORD-1001 当前状态：已发货。');
  expect(userMessage.compareDocumentPosition(activity) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(activity.compareDocumentPosition(assistantMessage) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

it('creates the first conversation when storage is empty', async () => {
  vi.mocked(api.listConversations).mockResolvedValue([]);
  vi.mocked(api.createConversation).mockResolvedValue({ id: 'new', title: '新会话', created_at: detail.created_at });
  vi.mocked(api.getConversation).mockResolvedValue({ ...detail, id: 'new', title: '新会话' });

  render(<StrictMode><App /></StrictMode>);

  await waitFor(() => expect(api.createConversation).toHaveBeenCalledTimes(1));
  expect(await screen.findByRole('heading', { name: '新会话' })).toBeInTheDocument();
});

it('submits a message and resolves an approval', async () => {
  const user = userEvent.setup();
  vi.mocked(api.createRun).mockResolvedValue({ run_id: 'r3', status: 'running' });
  vi.mocked(api.streamRunEvents).mockImplementation(async (_runId, _cursor, onEvent) => {
    onEvent({
      run_id: 'r3',
      sequence: 1,
      type: 'approval.required',
      data: { tool: 'create_todo' },
      created_at: detail.created_at,
    });
    return 1;
  });
  render(<App />);
  await screen.findByText('ZC Agent Desk');

  await user.type(screen.getByLabelText('发送消息'), '查询订单 ORD-9999');
  await user.click(screen.getByRole('button', { name: '发送' }));
  await waitFor(() => expect(api.createRun).toHaveBeenCalledWith('c1', '查询订单 ORD-9999', 'workflow'));

  await user.click(screen.getByRole('button', { name: '批准创建待办' }));
  await waitFor(() => expect(api.decideApproval).toHaveBeenCalledWith('r2', 'approve'));
  await waitFor(() => expect(api.getConversation).toHaveBeenCalledTimes(4));
  expect(api.listTodos).toHaveBeenCalledTimes(2);
});

it('persists Real Agent selection and sends it with the next message', async () => {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByText('ZC Agent Desk');

  await user.click(screen.getByRole('button', { name: 'Real Agent' }));
  expect(localStorage.getItem('zc-agent-desk.runtime')).toBe('hermes');
  await user.type(screen.getByLabelText('发送消息'), '真实回答');
  await user.click(screen.getByRole('button', { name: '发送' }));

  await waitFor(() => expect(api.createRun).toHaveBeenCalledWith('c1', '真实回答', 'hermes'));
});

it('falls back to Workflow when the stored Real Agent is unavailable', async () => {
  localStorage.setItem('zc-agent-desk.runtime', 'hermes');
  vi.mocked(api.getHealth).mockResolvedValue({
    status: 'ok',
    mode: 'auto',
    runtimes: {
      workflow: { available: true },
      hermes: { available: false, reason: 'Real Agent 尚未配置' },
    },
  });

  render(<App />);

  expect(await screen.findByRole('button', { name: 'Workflow' })).toHaveAttribute('aria-pressed', 'true');
  expect(localStorage.getItem('zc-agent-desk.runtime')).toBe('workflow');
  expect(screen.getByText('Real Agent 尚未配置')).toBeInTheDocument();
});

it('renders a streamed tool event before the run completes', async () => {
  const user = userEvent.setup();
  let finishStream!: () => void;
  const streamFinished = new Promise<void>((resolve) => { finishStream = resolve; });
  const runningDetail: ConversationDetail = {
    ...detail,
    messages: [
      ...detail.messages,
      { id: 'm3', role: 'user', content: '创建待办：检查录屏', run_id: 'r3', created_at: detail.created_at },
    ],
    runs: [
      ...detail.runs,
      { id: 'r3', conversation_id: 'c1', status: 'running', runtime_mode: 'hermes', pending_tool: null, pending_args: null, events: [] },
    ],
  };
  vi.mocked(api.createRun).mockResolvedValue({ run_id: 'r3', status: 'running' });
  vi.mocked(api.getConversation)
    .mockResolvedValueOnce(detail)
    .mockResolvedValue(runningDetail);
  vi.mocked(api.streamRunEvents).mockImplementation(async (_runId, _cursor, onEvent) => {
    onEvent({
      run_id: 'r3',
      sequence: 1,
      type: 'tool.started',
      data: { tool: 'create_todo' },
      created_at: detail.created_at,
    });
    await streamFinished;
    return 1;
  });

  render(<App />);
  await screen.findByText('ZC Agent Desk');
  await user.type(screen.getByLabelText('发送消息'), '创建待办：检查录屏');
  await user.click(screen.getByRole('button', { name: '发送' }));

  expect(await screen.findByRole('button', { name: /正在调用 创建待办/ })).toBeInTheDocument();
  finishStream();
});
