export type RunStatus =
  | 'queued'
  | 'running'
  | 'awaiting_approval'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type RuntimeMode = 'workflow' | 'hermes';

export interface RuntimeCapability {
  available: boolean;
  reason?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  run_id: string | null;
  created_at: string;
}

export interface RunEvent {
  run_id: string;
  sequence: number;
  type: string;
  data: Record<string, unknown>;
  created_at: string;
}

export interface Run {
  id: string;
  conversation_id: string;
  status: RunStatus;
  runtime_mode: RuntimeMode;
  pending_tool: string | null;
  pending_args: Record<string, unknown> | null;
  events: RunEvent[];
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
  runs: Run[];
}

export interface Todo {
  id: string;
  title: string;
  due_at: string | null;
  priority: string;
  created_at: string;
}

export interface RunCreated {
  run_id: string;
  status: RunStatus;
}

export interface ApprovalResult {
  run_id: string;
  status: RunStatus;
  replayed: boolean;
}

export interface Health {
  status: string;
  mode: 'auto' | 'mock' | 'hermes';
  runtimes: Record<RuntimeMode, RuntimeCapability>;
}
