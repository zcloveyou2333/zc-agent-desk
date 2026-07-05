import { useState } from 'react';
import { summarizeRun } from '../runActivity';
import type { Run } from '../types';

const toneIcon = {
  running: '↻',
  success: '✓',
  awaiting: '!',
  failed: '×',
  neutral: '✓',
};

const stepState = {
  running: '进行中',
  completed: '已完成',
  awaiting: '等待审批',
  failed: '失败',
};

export default function RunActivityCard({ run }: { run: Run }) {
  const [expanded, setExpanded] = useState(false);
  const activity = summarizeRun(run);
  const runtimeLabel = run.runtime_mode === 'hermes' ? 'Real Agent' : 'Workflow';
  const meta = [runtimeLabel, activity.duration, activity.steps.length ? `${activity.steps.length} 步` : null]
    .filter(Boolean)
    .join(' · ');

  return (
    <section className={`run-activity ${activity.tone}`} role={activity.tone === 'failed' ? 'alert' : undefined}>
      <button
        type="button"
        className="run-activity-toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((value) => !value)}
      >
        <span className="activity-icon" aria-hidden="true">{toneIcon[activity.tone]}</span>
        <span className="activity-summary">
          <strong>{activity.title}</strong>
          {meta && <small>{meta}</small>}
        </span>
        <span className="activity-chevron" aria-hidden="true">{expanded ? '⌃' : '⌄'}</span>
      </button>
      {expanded && (
        <div className="activity-details">
          {activity.detail && <p className="activity-error-detail">{activity.detail}</p>}
          {activity.steps.length === 0 && <p className="activity-empty">本轮没有工具调用。</p>}
          <ol>
            {activity.steps.map((step, index) => (
              <li className={`activity-step ${step.state}`} key={`${step.tool}-${index}`}>
                <span className="step-marker" aria-hidden="true" />
                <div>
                  <strong>{step.label}</strong>
                  <small>{stepState[step.state]}{step.duration ? ` · ${step.duration}` : ''}</small>
                  {step.arguments && <code>{JSON.stringify(step.arguments, null, 2)}</code>}
                  {step.result !== undefined && <code>{JSON.stringify(step.result, null, 2)}</code>}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}
