import { useState } from 'react';

interface Props {
  title: string;
  onDecision: (decision: 'approve' | 'reject') => Promise<void>;
}

export default function ApprovalCard({ title, onDecision }: Props) {
  const [pending, setPending] = useState(false);

  async function decide(decision: 'approve' | 'reject') {
    setPending(true);
    try {
      await onDecision(decision);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="approval-card" aria-label="待办审批">
      <div className="approval-icon">!</div>
      <div>
        <span className="approval-state">等待审批</span>
        <h3>创建待办</h3>
        <p>{title}</p>
        <div className="approval-actions">
          <button disabled={pending} onClick={() => decide('approve')}>批准创建待办</button>
          <button className="secondary" disabled={pending} onClick={() => decide('reject')}>拒绝</button>
        </div>
      </div>
    </section>
  );
}
