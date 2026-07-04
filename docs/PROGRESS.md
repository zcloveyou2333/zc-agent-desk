# Progress and Recovery

## Current gate

G0 - design and repository baseline.

## Completed

- Scope and architecture approved.
- Product name fixed as ZC Agent Desk, built by zcloveyou.
- Design, decisions, AI collaboration format, and recovery record created.

## Next action

Run G1 Hermes probes: pin a candidate commit, verify health/runs/events,
structured tool calls, project plugin loading, blocking approval, and the macOS
execution policy. Stop for approval with evidence if a mandatory probe fails.

## Recovery protocol

1. Read `docs/PROGRESS.md` and `docs/DECISIONS.md`.
2. Run `git status --short --branch` and inspect the last commit.
3. Run the verification command recorded for the active gate.
4. Continue only the active gate; do not start later work with an unverified
   working tree.

