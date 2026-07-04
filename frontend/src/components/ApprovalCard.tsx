import { useState } from 'react';

interface Props {
  tool: string;
  arguments: Record<string, unknown>;
  onDecision: (decision: 'approve' | 'reject') => Promise<void>;
}

const presentations: Record<string, { heading: string; approve: string }> = {
  create_todo: { heading: '创建待办', approve: '批准创建待办' },
  terminal: { heading: '执行终端命令', approve: '批准执行命令' },
  write_file: { heading: '写入文件', approve: '批准写入文件' },
  patch: { heading: '修改文件', approve: '批准修改文件' },
};

export default function ApprovalCard({ tool, arguments: args, onDecision }: Props) {
  const [pending, setPending] = useState(false);
  const presentation = presentations[tool] ?? { heading: `执行 ${tool}`, approve: '批准操作' };
  const summary = String(
    args.title ?? args.command ?? args.path ?? (args.mode === 'patch' ? '多文件补丁' : '请确认工具参数'),
  );

  async function decide(decision: 'approve' | 'reject') {
    setPending(true);
    try {
      await onDecision(decision);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="approval-card" aria-label="工具审批">
      <div className="approval-icon">!</div>
      <div>
        <span className="approval-state">等待审批</span>
        <h3>{presentation.heading}</h3>
        <p>{summary}</p>
        <div className="approval-actions">
          <button disabled={pending} onClick={() => decide('approve')}>{presentation.approve}</button>
          <button className="secondary" disabled={pending} onClick={() => decide('reject')}>拒绝</button>
        </div>
      </div>
    </section>
  );
}
