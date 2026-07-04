import type { RunEvent, Todo } from '../types';

const labels: Record<string, string> = {
  'tool.started': '工具开始',
  'tool.completed': '工具完成',
  'approval.required': '等待审批',
  'message.delta': '生成回复',
  'message.completed': '回复完成',
  'run.failed': '运行失败',
};

export default function Inspector({ events, todos }: { events: RunEvent[]; todos: Todo[] }) {
  return (
    <aside className="inspector">
      <section>
        <div className="panel-heading"><div><p className="section-label">执行过程</p><h2>Agent Trace</h2></div><span>{events.length} events</span></div>
        <div className="trace-list">
          {events.length === 0 && <p className="empty-state">发送消息后，这里会显示 Agent 生命周期。</p>}
          {events.map((event) => (
            <div className="trace-row" key={`${event.run_id}-${event.sequence}`}>
              <span className="trace-dot" />
              <div><strong>{labels[event.type] ?? event.type}</strong><small>#{event.sequence} · {String(event.data.tool ?? '')}</small></div>
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
