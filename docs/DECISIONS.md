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
