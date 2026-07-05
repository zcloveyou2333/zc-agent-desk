import { FormEvent, Fragment, useState } from 'react';
import type { ConversationDetail, RuntimeCapability, RuntimeMode } from '../types';
import ApprovalCard from './ApprovalCard';
import RunActivityCard from './RunActivityCard';
import RuntimeSwitch from './RuntimeSwitch';

interface Props {
  detail: ConversationDetail | null;
  busy: boolean;
  error: string | null;
  onSend: (message: string) => Promise<void>;
  onApproval: (runId: string, decision: 'approve' | 'reject') => Promise<void>;
  runtimeMode: RuntimeMode;
  hermes: RuntimeCapability;
  onRuntimeChange: (mode: RuntimeMode) => void;
}

export default function ChatWorkspace({ detail, busy, error, onSend, onApproval, runtimeMode, hermes, onRuntimeChange }: Props) {
  const [message, setMessage] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = message.trim();
    if (!value || busy) return;
    await onSend(value);
    setMessage('');
  }

  const linkedRunIds = new Set(detail?.messages.map((item) => item.run_id).filter(Boolean) ?? []);
  const fallbackPendingRuns = detail?.runs.filter(
    (run) => run.status === 'awaiting_approval' && !linkedRunIds.has(run.id),
  ) ?? [];

  return (
    <main className="chat-workspace">
      <header className="workspace-header">
        <div><p className="section-label">当前会话</p><h1>{detail?.title ?? '正在载入'}</h1></div>
        <span className="online-state">● 在线</span>
      </header>
      <div className="message-stream" aria-live="polite">
        {detail?.messages.map((item) => {
          const run = item.role === 'user' && item.run_id
            ? detail.runs.find((candidate) => candidate.id === item.run_id)
            : undefined;
          return (
            <Fragment key={item.id}>
              <article className={`message ${item.role}`}>
                <span className="message-role">{item.role === 'user' ? '你' : 'ZC'}</span>
                <div><p>{item.content}</p><time>{new Date(item.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</time></div>
              </article>
              {run && <RunActivityCard run={run} />}
              {run?.status === 'awaiting_approval' && (
                <ApprovalCard
                  tool={run.pending_tool ?? 'unknown_tool'}
                  arguments={run.pending_args ?? {}}
                  onDecision={(decision) => onApproval(run.id, decision)}
                />
              )}
            </Fragment>
          );
        })}
        {fallbackPendingRuns.map((run) => (
          <ApprovalCard
            key={run.id}
            tool={run.pending_tool ?? 'unknown_tool'}
            arguments={run.pending_args ?? {}}
            onDecision={(decision) => onApproval(run.id, decision)}
          />
        ))}
        {error && <div className="run-error" role="alert">{error}</div>}
      </div>
      <form className="composer" onSubmit={submit}>
        <RuntimeSwitch value={runtimeMode} hermes={hermes} onChange={onRuntimeChange} />
        <label htmlFor="message-input">发送消息</label>
        <textarea
          id="message-input"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="试试：查询订单 ORD-1001"
          rows={3}
        />
        <div className="composer-footer"><span>{runtimeMode === 'hermes' ? 'Real Agent · 模型自主选择工具' : 'Workflow · 预设流程，不消耗 API Key'}</span><button disabled={busy || !message.trim()}>{busy ? '处理中…' : '发送'}</button></div>
      </form>
    </main>
  );
}
