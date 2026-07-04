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

