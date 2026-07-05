import type { RuntimeCapability, RuntimeMode } from '../types';

interface Props {
  value: RuntimeMode;
  hermes: RuntimeCapability;
  onChange: (mode: RuntimeMode) => void;
}

export default function RuntimeSwitch({ value, hermes, onChange }: Props) {
  return (
    <div className="runtime-control">
      <div className="runtime-switch" aria-label="运行模式">
        <button
          type="button"
          aria-pressed={value === 'workflow'}
          onClick={() => onChange('workflow')}
        >
          Workflow
        </button>
        <button
          type="button"
          aria-pressed={value === 'hermes'}
          disabled={!hermes.available}
          title={!hermes.available ? hermes.reason : undefined}
          onClick={() => onChange('hermes')}
        >
          Real Agent
        </button>
      </div>
      {!hermes.available && hermes.reason && <small className="runtime-reason">{hermes.reason}</small>}
    </div>
  );
}
