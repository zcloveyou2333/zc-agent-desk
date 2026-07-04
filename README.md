# ZC Agent Desk

> Built by zcloveyou

ZC Agent Desk is an internal employee chatbot MVP built to demonstrate
multi-turn conversation, model-selected tools, explicit approval for write
operations, deterministic zero-key operation, and an optional Hermes-backed
agent runtime.

## Current status

Implementation is proceeding through explicit approval gates. The repository
currently contains the approved design and execution records. Runnable setup
instructions will be added with the G2 vertical slice and verified again at G4.

## Planned runtime modes

- `mock`: offline, deterministic, and suitable for evaluation without API keys.
- `hermes`: live OpenAI-compatible Chat Completions through a pinned Hermes
  sidecar.

See [the design](docs/DESIGN.md), [decisions](docs/DECISIONS.md), and
[implementation plan](docs/IMPLEMENTATION_PLAN.md).

## Security

Never commit `.env`, API keys, tokens, private account data, or unredacted
recordings. Local macOS command confinement is an MVP safeguard and is not
presented as a production-grade sandbox.

