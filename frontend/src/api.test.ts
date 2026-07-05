import {
  createConversation,
  createRun,
  decideApproval,
  getConversation,
  getHealth,
  listConversations,
  listTodos,
} from './api';

const jsonResponse = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

describe('API client', () => {
  it('uses the public conversation and todo endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse([{ id: 'c1' }]))
      .mockResolvedValueOnce(jsonResponse({ id: 'c2' }, 201))
      .mockResolvedValueOnce(jsonResponse({ id: 'c2', messages: [], runs: [] }))
      .mockResolvedValueOnce(jsonResponse([{ id: 't1' }]));
    vi.stubGlobal('fetch', fetchMock);

    await listConversations();
    await createConversation('新会话');
    await getConversation('c2');
    await listTodos();

    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/conversations', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/conversations',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ title: '新会话' }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(3, '/api/conversations/c2', expect.any(Object));
    expect(fetchMock).toHaveBeenNthCalledWith(4, '/api/todos', expect.any(Object));
  });

  it('posts runs and approval decisions', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ run_id: 'r1', status: 'completed' }, 202))
      .mockResolvedValueOnce(jsonResponse({ run_id: 'r1', status: 'completed', replayed: false }));
    vi.stubGlobal('fetch', fetchMock);

    await createRun('c1', '查询订单 ORD-1001', 'workflow');
    await decideApproval('r1', 'approve');

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/conversations/c1/runs',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ message: '查询订单 ORD-1001', mode: 'workflow' }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/runs/r1/approval',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ decision: 'approve' }) }),
    );
  });

  it('throws the backend detail for a failed request', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ detail: 'Run not found' }, 404)),
    );

    await expect(getConversation('missing')).rejects.toThrow('Run not found');
  });

  it('reads independent runtime capabilities', async () => {
    const health = {
      status: 'ok',
      mode: 'auto',
      runtimes: {
        workflow: { available: true },
        hermes: { available: false, reason: 'Real Agent 尚未配置' },
      },
    };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(health)));
    await expect(getHealth()).resolves.toEqual(health);
  });
});
