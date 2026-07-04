# Decision Log

## 2026-07-03

### Reuse Hermes without restructuring it

Hermes is a mature, fast-moving runtime whose core conversation loop is much
larger than this exercise. ZC Agent Desk integrates it through a versioned HTTP
adapter and project plugin instead of reorganizing upstream source into the
eleven explanatory lifecycle stages.

### Keep mock mode independent

The assignment requires the core flow to work without a real model key. The
mock runtime is deterministic, uses the same application contracts, and keeps
tests offline. Live Hermes remains a separately verified integration path.

### Require approval before effects

Business reads run automatically. Todo creation, terminal commands, and file
mutations wait for an explicit decision. A rejected or replayed approval must
not create side effects.

### Describe local execution honestly

Setting a working directory does not confine a shell. macOS developer tools are
allowed only after an operating-system policy probe passes. Other platforms
disable those tools while retaining the business chatbot.

### Isolate Hermes configuration

Project-plugin discovery requires `HERMES_ENABLE_PROJECT_PLUGINS=1`, while
activation separately requires `plugins.enabled`. ZC Agent Desk uses its own
project-local `HERMES_HOME` and config template so setup never mutates the
developer's personal `~/.hermes` profile.

### Use `MODEL_NAME` consistently

The live provider model is configured through `MODEL_NAME`, matching the
developer's existing projects. `OPENAI_MODEL` is not accepted as a second alias
because duplicate names make interrupted runs and setup instructions ambiguous.

### Lock a source archive by critical hashes

The manually downloaded Hermes 0.18.0 archive has no commit metadata. The
project records the archive version and SHA-256 values for the package manifest,
API server, and plugin loader. A future Git-based setup may replace this with an
exact commit after compatibility tests pass.

### Bind relay credentials to a named custom provider

Hermes 0.18 protects credentials by refusing to forward the generic
`OPENAI_API_KEY` from a bare custom provider to a non-OpenAI host. ZC Agent Desk
uses the named provider `custom:zc-relay` with `key_env: OPENAI_API_KEY`. This
keeps the secret in the environment while making its intended recipient
explicit.

### Use Hermes manual approval mode

Hermes 0.18 supports `manual`, `smart`, and `off`; `ask` is invalid and only
falls back to `manual` with a warning. The pinned template uses `manual`, and a
live dangerous-command probe verified request, denial, and run resumption.

### Keep Mock routing deterministic and explicit

Mock mode recognizes the assignment's demonstration intents without calling a
model. This makes zero-key operation honest and the order, approval, rejection,
replay, and cancellation tests repeatable. Hermes owns model-selected routing
only in live mode.

### Use a light enterprise-console interface

Three visual directions were compared. The light blue-gray console was selected
because business flow, approval state, and Agent Trace are readable to both HR
and engineering reviewers during an 8–12 minute recording. Desktop uses three
columns; narrow screens preserve chat priority and stack the inspector.

### Preserve React StrictMode with guarded initialization

Browser acceptance found that an asynchronous empty-state initializer created
two conversations under StrictMode's development probe. StrictMode remains
enabled; a synchronous ref guard makes the bootstrap effect run once and a
regression test verifies that behavior.

### Correlate plugin calls with the application run ID

FastAPI passes its local run ID as Hermes `session_id`. Hermes forwards that
value to project tool handlers and hooks, so the authenticated bridge can attach
approval proposals to the correct persisted run without changing upstream
Hermes or exposing a second public correlation API.

### Let the project policy own developer-tool approval

Hermes manual approval only covers commands it classifies as dangerous. The
assignment requires every terminal, write, and patch invocation to pause, so a
project `pre_tool_call` hook performs path checks and blocks on the application
approval endpoint. Native approval is set to `off` to prevent duplicate prompts;
the macOS operating-system policy remains an independent containment layer.

### Treat not-found orders as business results

The internal bridge returns `{found: false}` with HTTP 200 for an unknown order.
HTTP errors are reserved for authentication and infrastructure failures, so the
model can distinguish a missing order from an unavailable backend.

### Collapse token deltas in the visual Trace

All deltas remain persisted and replayable, but consecutive `message.delta`
events render as one “生成回复” lifecycle row. This preserves protocol evidence
without turning a short live answer into dozens of visually identical rows.
