# AI Collaboration Record

This document records material AI-assisted decisions rather than raw chat logs.
Secrets, private prompts, and unrelated machine information are excluded.

| Topic | AI suggestion | Decision | Reason and verification |
| --- | --- | --- | --- |
| Agent runtime | Refactor Hermes into eleven Claude Code Unpacked stages | Rejected | Those stages describe request flow, not stable module boundaries; the fork cost does not improve the required MVP. |
| Integration | Run Hermes as a sidecar behind an adapter | Accepted | Preserves an explicit product/runtime boundary and permits a zero-Hermes mock mode. G1 must verify the pinned API. |
| Mock mode | Skip mock because a live key exists | Rejected | Zero-key operation is an explicit assignment requirement and is needed for deterministic tests. |
| Write tools | Execute todo creation immediately | Rejected | A write effect must pause before persistence and record approval or rejection. |
| Local shell | Treat `cwd` as a sandbox | Rejected | A local shell can leave its starting directory. The project requires a macOS policy probe and honest limitations. |
| Hermes plugin activation | Set only `HERMES_ENABLE_PROJECT_PLUGINS=1` | Modified | A live discovery probe showed this only enables scanning; `plugins.enabled` is also required, so the project isolates and supplies both settings. |
| Public environment template | Mirror the private `.env`, including a fake key shaped like a secret | Rejected | The public template uses generic placeholders so secret scanners stay meaningful and provider details are not accidentally published. |
| Relay authentication | Keep bare `provider: custom` and rely on `OPENAI_API_KEY` fallback | Rejected | Hermes intentionally withholds that credential from third-party hosts. A named provider with `key_env` passed live text and tool-call probes without storing the key. |
| Approval config | Use conceptual value `ask` | Modified | Hermes 0.18 only supports `manual`, `smart`, and `off`. The template now uses `manual`, verified by a live request-and-deny flow. |
| Mock agent behavior | Make mock responses random or model-like | Rejected | Explicit deterministic routing produces honest zero-key behavior and repeatable acceptance tests while preserving the same public run/tool/approval contracts. |
| Frontend direction | Use a dark developer-terminal aesthetic | Rejected | The selected light enterprise console makes approvals and Trace legible to a mixed HR/engineering audience during recording. |
| Duplicate initial conversations | Disable React StrictMode | Rejected | A browser probe revealed the duplicate effect. Initialization is guarded and regression-tested while StrictMode remains useful. |

Future entries use the same format: suggestion, adoption/modification/rejection,
rationale, and concrete verification evidence.
