import type { Run, RunEvent } from './types';

export type ActivityTone = 'running' | 'success' | 'awaiting' | 'failed' | 'neutral';
export type ActivityStepState = 'running' | 'completed' | 'awaiting' | 'failed';

export interface ActivityStep {
  tool: string;
  label: string;
  state: ActivityStepState;
  arguments?: Record<string, unknown>;
  result?: unknown;
  duration?: string;
}

export interface RunActivity {
  tone: ActivityTone;
  title: string;
  duration?: string;
  detail?: string;
  steps: ActivityStep[];
}

const TOOL_LABELS: Record<string, string> = {
  query_mock_business: '查询业务订单',
  create_todo: '创建待办',
  terminal: '执行终端命令',
  write_file: '修改文件',
  patch: '修改文件',
  apply_patch: '修改文件',
};

const SENSITIVE_KEY = /key|token|secret|authorization|password/i;

export function toolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? tool;
}

function truncate(value: string): string {
  return value.length > 160 ? `${value.slice(0, 157)}…` : value;
}

function sanitizeValue(value: unknown): unknown {
  if (typeof value === 'string') return truncate(value);
  if (Array.isArray(value)) return value.map(sanitizeValue);
  if (value && typeof value === 'object') return formatArguments(value as Record<string, unknown>);
  return value;
}

export function formatArguments(argumentsValue: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(argumentsValue).map(([key, value]) => [
      key,
      SENSITIVE_KEY.test(key) ? '[已隐藏]' : sanitizeValue(value),
    ]),
  );
}

function seconds(value: unknown): string | undefined {
  return typeof value === 'number' ? `${value.toFixed(2)} 秒` : undefined;
}

function eventTool(event: RunEvent): string {
  return String(event.data.tool ?? 'unknown_tool');
}

export function summarizeRun(run: Run): RunActivity {
  const steps: ActivityStep[] = [];
  for (const event of run.events) {
    if (event.type === 'tool.started') {
      const tool = eventTool(event);
      steps.push({
        tool,
        label: toolLabel(tool),
        state: 'running',
        ...(event.data.arguments && typeof event.data.arguments === 'object'
          ? { arguments: formatArguments(event.data.arguments as Record<string, unknown>) }
          : {}),
      });
    } else if (event.type === 'tool.completed') {
      const tool = eventTool(event);
      const step = [...steps].reverse().find((item) => item.tool === tool && item.state === 'running');
      const completed: ActivityStep = step ?? { tool, label: toolLabel(tool), state: 'running' };
      completed.state = event.data.error === true ? 'failed' : 'completed';
      completed.duration = seconds(event.data.duration);
      if ('result' in event.data) completed.result = sanitizeValue(event.data.result);
      if (!step) steps.push(completed);
    } else if (event.type === 'approval.required') {
      const tool = eventTool(event);
      const step = [...steps].reverse().find((item) => item.tool === tool && item.state === 'running');
      if (step) step.state = 'awaiting';
      else steps.push({ tool, label: toolLabel(tool), state: 'awaiting' });
    }
  }

  const failure = [...run.events].reverse().find((event) => event.type === 'run.failed');
  if (failure || run.status === 'failed' || steps.some((step) => step.state === 'failed')) {
    return {
      tone: 'failed',
      title: failure ? '模型请求失败' : '工具执行失败',
      detail: typeof failure?.data.message === 'string' ? truncate(failure.data.message) : undefined,
      steps,
    };
  }
  if (run.status === 'awaiting_approval' || steps.some((step) => step.state === 'awaiting')) {
    return { tone: 'awaiting', title: '等待你的审批', steps };
  }
  const active = [...steps].reverse().find((step) => step.state === 'running');
  if (run.status === 'running' || active) {
    return { tone: 'running', title: active ? `正在调用 ${active.label}…` : '正在处理…', steps };
  }
  const completed = steps.filter((step) => step.state === 'completed');
  const totalDuration = completed.reduce((sum, step) => sum + Number.parseFloat(step.duration ?? '0'), 0);
  return {
    tone: completed.length ? 'success' : 'neutral',
    title: completed.length ? `已完成 ${completed.length} 个工具调用` : '运行已完成',
    duration: totalDuration ? `${totalDuration.toFixed(2)} 秒` : undefined,
    steps,
  };
}
