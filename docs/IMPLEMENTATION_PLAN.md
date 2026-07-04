# ZC Agent Desk Implementation Plan

## Approval gates

- G0: repository, design, decisions, and recovery baseline.
- G1: pinned Hermes/API/plugin/approval/macOS-policy feasibility.
- G2: deterministic mock vertical slice and reviewable UI.
- G3: live Hermes integration and developer-tool security tests.
- G4: release candidate, clean-clone verification, documentation, and secret scan.
- G5: user-approved public repository and video submission.

## Execution order

1. Establish backend contracts and SQLite persistence with test-first cycles.
2. Implement mock runs, tools, approval, SSE replay, and cancellation.
3. Build the React client against those verified contracts.
4. Add the pinned Hermes adapter and project plugin after G1 feasibility passes.
5. Add macOS-only execution policy and negative security tests.
6. Run full backend, frontend, end-to-end, build, and release checks.

Every behavior change starts with a failing test. Each gate ends with fresh
verification output and a small commit before work moves forward.

