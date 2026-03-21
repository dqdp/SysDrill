# Slice 008e: Stale Recommendation Recovery And Reload Smoke

## Status

- completed

## Goal

Close the remaining launcher-shell gap so that:
- a browser-restored recommendation does not leave the learner stuck when the
  backend no longer recognizes its `decision_id`
- reload/recovery behavior is covered by one higher-level frontend smoke
  scenario inside the existing Vitest harness
- the repository explicitly documents that current recommendation/session
  persistence is browser-local and temporary

## Affected bounded contexts

- `web_api / ui`
- narrow consumption of existing `recommendation_engine` and `session_runtime`
  surfaces

## Non-goals

- no backend API or contract changes
- no durable recommendation/session persistence across devices or backend
  restarts
- no new recommendation lifecycle events
- no new browser automation stack beyond the current frontend test harness

## Constraints

- recommendation remains backend-generated; the UI may only cache and replay a
  previously shown decision
- stale recommendation recovery must not silently resubmit a different action
- explicit user reset remains the only path that intentionally fetches a fresh
  launcher state without first attempting recovery
- the existing v2.2 runtime and recommendation contracts remain unchanged

## Architectural approaches considered

### Option A: UI detects stale recommended-start failures and refreshes launcher recommendation

- treat `POST /runtime/sessions/start-from-recommendation` `404` responses as
  “stored recommendation is no longer launchable”
- clear the cached recommendation, request a fresh recommendation, and keep the
  learner on the launcher with an explicit message
- keep the implementation inside the current React/Vitest surface

Trade-offs:
- minimal and contract-preserving
- recovers from backend process-local recommendation loss without adding a new
  preflight endpoint
- still depends on browser-local state and on the backend returning `404` for
  stale decisions

### Option B: Add backend preflight or durable recommendation validation

- introduce a validation/readback endpoint or persist recommendation decisions
  durably

Trade-offs:
- cleaner long-term ownership
- expands backend contracts and storage requirements
- too broad for the current hardening slice

Decision:
- choose Option A

## Test contract

### 1. Stale recommendation recovery

Given:
- a shown recommendation exists in local storage
- the learner clicks `Start recommended session`
- `POST /runtime/sessions/start-from-recommendation` returns `404`

Then:
- the UI clears the stale cached recommendation
- the UI requests a fresh recommendation
- the learner remains on the launcher
- the launcher shows the fresh recommendation and an explicit recovery message

### 2. Reload/recovery smoke

Given:
- a learner starts a session, producing browser-local resume state
- the page reloads before review is shown
- backend state now requires review recovery

Then:
- the reloaded app restores the saved session
- the app reaches review without resubmitting the answer
- returning to the launcher clears active session resume state

### 3. Documentation boundary

Given:
- a frontend engineer follows the local shell README

Then:
- the README states that recommendation is implemented in the shell
- the README states that `/recommendations` is proxied in local dev
- the README states that current session/recommendation persistence is
  browser-local and temporary

## Acceptance criteria

- stale cached recommendation no longer leaves the launcher in a broken state
- one smoke-style frontend scenario covers reload/recovery end to end
- frontend docs reflect the current launcher shell behavior and persistence
  boundary
- frontend tests and production build pass

## Weak spots review

- stale recommendation recovery still cannot distinguish “unknown decision” from
  other `404` launch failures without backend-specific detail inspection; this
  slice accepts that narrow ambiguity to avoid contract changes
- browser-local persistence remains best-effort and single-device only
- the smoke scenario is higher-level but still runs in jsdom rather than a real
  browser process

## Source-of-truth review

- `docs/00_change_protocol.md`: implementation-only change; ADR not required
- `docs/03_architecture/recommendation_engine_surface.md`: preserved
- `docs/03_architecture/session_runtime_state_machine_v1.md`: preserved
