import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as api from './api';
import type { Conversation, ConversationDetail, RunEvent, Todo } from './types';
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
  const [runtimeMode, setRuntimeMode] = useState<'mock' | 'hermes'>('mock');
  const initialized = useRef(false);

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
    if (initialized.current) return;
    initialized.current = true;
    Promise.all([
      refreshConversations(),
      api.listTodos().then(setTodos),
      api.getHealth().then((health) => setRuntimeMode(health.mode)),
    ]).catch((reason) => {
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
      await loadDetail(activeId);
      if (run.status !== 'awaiting_approval') {
        await api.streamRunEvents(run.run_id, 0, (event) => {
          mergeRunEvent(event);
        });
      }
      await loadDetail(activeId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '消息发送失败');
      throw reason;
    } finally {
      setBusy(false);
    }
  }

  function mergeRunEvent(event: RunEvent) {
    setDetail((current) => {
      if (!current) return current;
      const runs = current.runs.map((run) => {
        if (run.id !== event.run_id) return run;
        if (run.events.some((existing) => existing.sequence === event.sequence)) return run;
        const events = [...run.events, event].sort((left, right) => left.sequence - right.sequence);
        if (event.type === 'approval.required') {
          return {
            ...run,
            status: 'awaiting_approval' as const,
            pending_tool: String(event.data.tool ?? run.pending_tool ?? 'unknown_tool'),
            pending_args: (event.data.arguments as Record<string, unknown> | undefined) ?? run.pending_args,
            events,
          };
        }
        if (event.type === 'run.failed') return { ...run, status: 'failed' as const, events };
        return { ...run, events };
      });
      return { ...current, runs };
    });
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
      <ConversationRail conversations={conversations} activeId={activeId} onSelect={selectConversation} onCreate={createConversation} runtimeMode={runtimeMode} />
      <ChatWorkspace detail={detail} busy={busy} error={error} onSend={sendMessage} onApproval={decide} runtimeMode={runtimeMode} />
      <Inspector events={events} todos={todos} />
    </div>
  );
}
