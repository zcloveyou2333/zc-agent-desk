import { useCallback, useEffect, useMemo, useState } from 'react';
import * as api from './api';
import type { Conversation, ConversationDetail, Todo } from './types';
import ChatWorkspace from './components/ChatWorkspace';
import ConversationRail from './components/ConversationRail';
import Inspector from './components/Inspector';

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDetail = useCallback(async (id: string) => {
    const next = await api.getConversation(id);
    setDetail(next);
  }, []);

  const refreshConversations = useCallback(async () => {
    let items = await api.listConversations();
    if (items.length === 0) {
      const created = await api.createConversation('新会话');
      items = [created];
    }
    setConversations(items);
    const selected = activeId && items.some((item) => item.id === activeId) ? activeId : items[0].id;
    setActiveId(selected);
    await loadDetail(selected);
  }, [activeId, loadDetail]);

  useEffect(() => {
    Promise.all([refreshConversations(), api.listTodos().then(setTodos)]).catch((reason) => {
      setError(reason instanceof Error ? reason.message : '载入失败');
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function createConversation() {
    setError(null);
    const created = await api.createConversation('新会话');
    setConversations((current) => [created, ...current]);
    setActiveId(created.id);
    await loadDetail(created.id);
  }

  async function selectConversation(id: string) {
    setActiveId(id);
    setError(null);
    await loadDetail(id);
  }

  async function sendMessage(message: string) {
    if (!activeId) return;
    setBusy(true);
    setError(null);
    try {
      const run = await api.createRun(activeId, message);
      if (run.status !== 'awaiting_approval') {
        await api.streamRunEvents(run.run_id, 0, () => undefined);
      }
      await loadDetail(activeId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '消息发送失败');
      throw reason;
    } finally {
      setBusy(false);
    }
  }

  async function decide(runId: string, decision: 'approve' | 'reject') {
    if (!activeId) return;
    setError(null);
    try {
      await api.decideApproval(runId, decision);
      const [nextTodos] = await Promise.all([api.listTodos(), loadDetail(activeId)]);
      setTodos(nextTodos);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '审批失败');
      throw reason;
    }
  }

  const events = useMemo(() => detail?.runs.flatMap((run) => run.events) ?? [], [detail]);

  return (
    <div className="app-shell">
      <ConversationRail conversations={conversations} activeId={activeId} onSelect={selectConversation} onCreate={createConversation} />
      <ChatWorkspace detail={detail} busy={busy} error={error} onSend={sendMessage} onApproval={decide} />
      <Inspector events={events} todos={todos} />
    </div>
  );
}
