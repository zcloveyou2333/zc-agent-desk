import type { RunEvent, Todo } from '../types';
import { toolLabel } from '../runActivity';

const labels: Record<string, string> = {
  'tool.started': '工具开始',
  'tool.completed': '工具完成',
  'approval.required': '等待审批',
  'message.delta': '生成回复',
  'message.completed': '回复完成',
  'run.failed': '运行失败',
};

export default function Inspector({ events, todos }: { events: RunEvent[]; todos: Todo[] }) {
  const displayEvents = events.filter((event, index) => {
    if (event.type !== 'message.delta') return true;
    const previous = events[index - 1];
    return !previous || previous.type !== 'message.delta' || previous.run_id !== event.run_id;
  });
  return (
    <aside className="inspector">
      <section>
        <div className="panel-heading"><div><p className="section-label">执行过程</p><h2>Agent Trace</h2></div><span>{displayEvents.length} events</span></div>
        <div className="trace-list">
          {displayEvents.length === 0 && <p className="empty-state">发送消息后，这里会显示 Agent 生命周期。</p>}
          {displayEvents.map((event) => (
            <div
              className={`trace-row ${event.type === 'run.failed' || (event.type === 'tool.completed' && event.data.error === true) ? 'failed' : ''}`}
              key={`${event.run_id}-${event.sequence}`}
            >
              <span className="trace-dot" />
              <div>
                <strong>{event.type === 'tool.completed' && event.data.error === true ? '工具执行失败' : labels[event.type] ?? event.type}</strong>
                <small>#{event.sequence}{event.data.tool ? ` · ${toolLabel(String(event.data.tool))}` : ''}</small>
                {event.type === 'run.failed' && typeof event.data.message === 'string' && (
                  <details className="trace-error-detail">
                    <summary>查看失败详情</summary>
                    <p>{event.data.message}</p>
                  </details>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="todo-panel">
        <div className="panel-heading"><div><p className="section-label">已保存</p><h2>待办</h2></div><span>{todos.length}</span></div>
        {todos.length === 0 && <p className="empty-state">批准后的待办会显示在这里。</p>}
        {todos.map((todo) => <div className="todo-item" key={todo.id}><span>✓</span><div><strong>{todo.title}</strong><small>{todo.priority}</small></div></div>)}
      </section>
    </aside>
  );
}
