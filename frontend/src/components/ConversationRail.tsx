import type { Conversation } from '../types';

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  hermesAvailable: boolean;
}

export default function ConversationRail({ conversations, activeId, onSelect, onCreate, hermesAvailable }: Props) {
  return (
    <aside className="conversation-rail">
      <header className="brand-block">
        <div className="brand-mark">ZC</div>
        <div>
          <strong>ZC Agent Desk</strong>
          <small>Built by zcloveyou</small>
        </div>
      </header>
      <div className="runtime-badge"><span /> {hermesAvailable ? 'Workflow + Real' : 'Workflow Runtime'}</div>
      <button className="new-conversation" onClick={onCreate}>＋ 新建会话</button>
      <nav aria-label="会话列表">
        <p className="section-label">会话</p>
        {conversations.map((conversation) => (
          <button
            className={`conversation-item ${activeId === conversation.id ? 'active' : ''}`}
            key={conversation.id}
            onClick={() => onSelect(conversation.id)}
          >
            <span>{conversation.title}</span>
            <small>{new Date(conversation.created_at).toLocaleDateString('zh-CN')}</small>
          </button>
        ))}
      </nav>
    </aside>
  );
}
