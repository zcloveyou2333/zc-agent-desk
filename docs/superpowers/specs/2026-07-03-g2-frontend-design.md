# G2 Frontend Design

## Objective

Build a reviewable React interface for the deterministic Mock Runtime. The UI
must make conversation context, tool execution, approval boundaries, event
order, and persisted todos understandable during an interview recording.

The selected visual direction is a light blue-gray enterprise console. It is
preferred over a dark developer terminal because the product flow is easier
for both engineering and non-engineering reviewers to scan.

## Layout

The desktop interface uses three columns:

1. The left rail contains the ZC Agent Desk identity, `Built by zcloveyou`, the
   active runtime badge, a new-conversation action, and persisted conversations.
2. The center workspace contains the active conversation, message stream,
   inline approval cards, run errors, and message composer.
3. The right inspector contains the ordered Agent Trace and the persisted todo
   list. It explains what happened without exposing raw internal logs.

On narrow screens, the columns become a vertical sequence. Conversation and
composer remain first; Trace and todos follow so the primary task stays usable.

## Components and Boundaries

- `App` owns initial loading, active-conversation selection, and API state.
- `ConversationRail` renders and creates conversations.
- `ChatWorkspace` renders messages, the composer, pending state, and errors.
- `ApprovalCard` renders the proposed `create_todo` arguments and sends exactly
  one approve or reject decision while disabling repeated clicks.
- `TracePanel` maps normalized run events to human-readable lifecycle rows.
- `TodoPanel` renders persisted todos returned by the backend.
- `api.ts` owns HTTP and SSE transport. Components do not construct endpoints
  or interpret wire-level SSE frames.

The frontend does not reproduce the Mock Runtime's intent routing. FastAPI
remains the source of truth for run status, events, approval state, and effects.

## Interaction and Data Flow

On startup, the client loads conversations. If none exist, it creates one. It
then loads the selected conversation and todos from SQLite-backed APIs.

Submitting a message creates a run. The client immediately reloads persisted
state and subscribes to that run's SSE endpoint. Each event is keyed by its
monotonic sequence. Reconnection sends `Last-Event-ID`, so replayed events do
not create duplicate Trace rows or message fragments.

An `approval.required` event produces an inline card. Approve or reject calls
the approval API, disables the card while pending, then reloads the
conversation and todos. Backend idempotency remains authoritative if a request
is retried after a network interruption.

Refreshing the page reconstructs messages, runs, Trace, pending approvals, and
todos exclusively from persisted backend state.

## Errors and Accessibility

Errors belong to the affected run and are shown near the conversation rather
than as blocking global dialogs. A failed request retains the user's input and
offers retry. Controls have visible focus states, text labels, and disabled
states. Status is never communicated by color alone.

## Verification

Component tests cover initial conversation creation, message submission,
approval and rejection, Trace rendering, and persisted-state restoration. A
browser acceptance pass covers ordinary chat, existing and missing orders,
todo approval, todo rejection, refresh recovery, and responsive layout. The
production build must complete without warnings that affect runtime behavior.

## Exclusions

G2 does not add authentication, deployment, theme switching, message editing,
file uploads, RAG, or Hermes-specific developer tools. Those would dilute the
interview's core flow or belong to later gates.
