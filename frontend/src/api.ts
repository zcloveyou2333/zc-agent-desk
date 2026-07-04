import type {
  ApprovalResult,
  Conversation,
  ConversationDetail,
  Health,
  RunCreated,
  RunEvent,
  Todo,
} from './types';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const listConversations = () => request<Conversation[]>('/api/conversations');

export const createConversation = (title: string) =>
  request<Conversation>('/api/conversations', {
    method: 'POST',
    body: JSON.stringify({ title }),
  });

export const getConversation = (id: string) =>
  request<ConversationDetail>(`/api/conversations/${id}`);

export const createRun = (conversationId: string, message: string) =>
  request<RunCreated>(`/api/conversations/${conversationId}/runs`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });

export const decideApproval = (runId: string, decision: 'approve' | 'reject') =>
  request<ApprovalResult>(`/api/runs/${runId}/approval`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  });

export const listTodos = () => request<Todo[]>('/api/todos');
export const getHealth = () => request<Health>('/api/health');

export async function streamRunEvents(
  runId: string,
  lastEventId: number,
  onEvent: (event: RunEvent) => void,
  signal?: AbortSignal,
): Promise<number> {
  const response = await fetch(`/api/runs/${runId}/events`, {
    headers: lastEventId > 0 ? { 'Last-Event-ID': String(lastEventId) } : {},
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`SSE connection failed (${response.status})`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let cursor = lastEventId;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split('\n\n');
    buffer = blocks.pop() ?? '';
    for (const block of blocks) {
      if (!block || block.startsWith(':')) continue;
      const lines = block.split('\n');
      const sequence = Number(lines.find((line) => line.startsWith('id:'))?.slice(3).trim());
      if (!Number.isFinite(sequence) || sequence <= cursor) continue;
      const type = lines.find((line) => line.startsWith('event:'))?.slice(6).trim() ?? 'message';
      const dataText = lines.find((line) => line.startsWith('data:'))?.slice(5).trim() ?? '{}';
      cursor = sequence;
      onEvent({ run_id: runId, sequence, type, data: JSON.parse(dataText), created_at: new Date().toISOString() });
    }
    if (done) break;
  }
  return cursor;
}
