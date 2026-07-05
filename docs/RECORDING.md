# Recording Checklist (8–12 minutes)

## Before recording

- Use a clean browser profile or hide bookmarks, account names, notifications,
  terminal history, `.env`, provider URLs, and API dashboards.
- Start once in `auto` mode. Keep Workflow selected first; show Real Agent only
  if the relay is responsive.
- Run the verification commands in README and keep the final summary visible.
- Confirm the repository contains no local absolute paths, keys, tokens, or
  private screenshots with `python scripts/release_check.py`.

## Suggested timeline

1. **0:00–1:15 — Problem and scope.** Explain the employee-chatbot goal, the
   required zero-key path, and why login, RAG, deployment, and multi-user
   permissions were excluded.
2. **1:15–2:30 — Architecture.** Show `docs/ARCHITECTURE.md`: React/FastAPI,
   SQLite, replaceable Mock/Hermes runtimes, plugin boundary, and lifecycle
   Trace. State that Hermes was reused rather than rewritten.
3. **2:30–4:30 — Workflow acceptance.** State that Workflow is the required
   zero-key Mock path. Demonstrate `关键词分析` with its six visible steps, then
   an order or approval-gated todo; show the inline run card and Trace.
4. **4:30–6:30 — AI collaboration judgment.** Show three concrete entries in
   `docs/AI_COLLABORATION.md`: reject an eleven-folder Hermes refactor, retain
   deterministic Mock mode, and replace `cwd`-as-sandbox with tested policy.
   Mention the live bugs found and regression-tested instead of hiding them.
5. **6:30–8:30 — Real Agent path.** Switch in the same composer without a
   restart. If available, demonstrate model-selected order lookup and one
   approval-gated tool. Explain that results return to the model before its
   final answer. If unavailable, show the disabled capability and recorded G3
   evidence; do not imply a live run.
6. **8:30–10:00 — Verification and limits.** Show automated tests/build,
   release scan, fixed upstream commit, zero-key startup, current relay and
   macOS-sandbox limitations, and the next production steps.

## Final privacy review

- Watch the exported video once at normal speed and once while scrubbing frame
  by frame around terminal/editor transitions.
- Verify no `.env`, shell history, token, provider account, personal username,
  notification, browser profile, or local filesystem path is legible.
- Open every submitted link in a logged-out/incognito browser before sending it
  to HR.
