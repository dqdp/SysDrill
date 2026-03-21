# Slice 008d: Restore Error UX And Recommendation Resume

## Status

- in progress

## Goal

Tighten the frontend launcher/session shell so that:
- non-404 session-restore failures are surfaced explicitly to the learner
- launcher recommendation survives page refresh without forcing a new
  `POST /recommendations/next`

## Affected bounded contexts

- `web_api / ui`
- narrow consumption of the existing `recommendation_engine` surface
- narrow consumption of the existing `session_runtime` read surface

## Non-goals

- no backend contract changes
- no durable recommendation storage guarantees across backend restarts
- no new recommendation lifecycle events
- no server-side drafts or session resume model changes

## Constraints

- runtime remains the source of truth for active sessions
- recommendation remains a backend-generated structured action, never
  client-derived
- refresh-safe recommendation behavior must not silently generate a new
  recommendation decision on initial reload
- explicit user reset may still request a fresh recommendation

## Architectural approaches considered

### Option A: UI-local error state plus UI-local recommendation cache

- keep restore/session errors in UI state
- keep the shown recommendation decision in local storage until explicit reset
  or session start
- on initial launcher load, prefer the stored shown recommendation over a fresh
  backend call

Trade-offs:
- minimal scope
- preserves bounded-context ownership
- recommendation may become stale if the backend process restarted

### Option B: Always refetch recommendation and annotate restore errors only

- show restore errors explicitly
- never persist shown recommendation; always issue a new recommendation request

Trade-offs:
- simpler
- loses refresh safety and may generate extra recommendation decisions on reload
- conflicts with the intended “resume the shown decision” UX

Decision:
- choose Option A

## Test contract

### 1. Restore failure UX

Given:
- an active session envelope exists in local storage
- `GET /runtime/sessions/{id}` fails with a non-404 error

Then:
- the UI shows an explicit restore error
- the saved session is not silently discarded
- the learner can retry session restore
- the learner can discard the saved session and continue to the launcher

### 2. Refresh-safe recommendation

Given:
- no active session envelope exists
- a shown recommendation decision exists in local storage

Then:
- the launcher shows that stored recommendation on reload
- the frontend does not call `POST /recommendations/next` during initial reload
- manual launcher options may still load as normal

## Acceptance criteria

- restore failures are explicit and actionable
- stale recommendation generation on simple refresh is avoided
- explicit reset/start paths can still clear the stored recommendation and fetch
  a new one later
- frontend tests and production build pass

## Weak spots review

- stored recommendation is only refresh-safe within the browser, not durable
  against backend process restart
- recommendation acceptance may still fail if the stored decision is no longer
  known to the backend; this slice does not add a server-side validation
  preflight
- if future product scope needs cross-device or durable recommendation resume,
  that requires a new contract

## Source-of-truth review

- `docs/00_change_protocol.md`: implementation-only change; ADR not required
- `docs/03_architecture/recommendation_engine_surface.md`: preserved
- `docs/03_architecture/implementation_mapping_v1.md`: preserved
