import { FormEvent, useState } from 'react';
import type { ConversationDetail } from '../types';
import ApprovalCard from './ApprovalCard';

interface Props {
  detail: ConversationDetail | null;
  busy: boolean;
  error: string | null;
  onSend: (message: string) => Promise<void>;
  onApproval: (runId: string, decision: 'approve' | 'reject') => Promise<void>;
}

export default function ChatWorkspace({ detail, busy, error, onSend, onApproval }: Props) {
  const [message, setMessage] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = message.trim();
    if (!value || busy) return;
    await onSend(value);
    setMessage('');
  }

  const pendingRuns = detail?.runs.filter((run) => run.status === 'awaiting_approval') ?? [];

  return (
    <main className="chat-workspace">
      <header className="workspace-header">
        <div><p className="section-label">当前会话</p><h1>{detail?.title ?? '正在载入'}</h1></div>
        <span className="online-state">● 在线</span>
      </header>
      <div className="message-stream" aria-live="polite">
        {detail?.messages.map((item) => (
          <article className={`message ${item.role}`} key={item.id}>
            <span className="message-role">{item.role === 'user' ? '你' : 'ZC'}</span>
            <div><p>{item.content}</p><time>{new Date(item.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</time></div>
          </article>
        ))}
        {pendingRuns.map((run) => (
          <ApprovalCard
            key={run.id}
            title={run.pending_args?.title ?? '未命名待办'}
            onDecision={(decision) => onApproval(run.id, decision)}
          />
        ))}
        {error && <div className="run-error" role="alert">{error}</div>}
      </div>
      <form className="composer" onSubmit={submit}>
        <label htmlFor="message-input">发送消息</label>
        <textarea
          id="message-input"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="试试：查询订单 ORD-1001"
          rows={3}
        />
        <div><span>Mock 模式 · 不消耗 API Key</span><button disabled={busy || !message.trim()}>{busy ? '处理中…' : '发送'}</button></div>
      </form>
    </main>
  );
}
