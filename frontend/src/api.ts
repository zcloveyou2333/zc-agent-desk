import type {
  ApprovalResult,
  Conversation,
  ConversationDetail,
  RunCreated,
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
