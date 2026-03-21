# Slice 008c: Session Resume / Reload Semantics

## Status

- in progress

## Goal

Restore the current frontend session after reload/navigation using the existing
backend runtime/review endpoints and a minimal UI-local persistence envelope.

## Affected bounded contexts

- `web_api / ui`
- existing `session_runtime` read surface consumption

## Non-goals

- no new backend endpoints
- no backend-owned answer drafts
- no cross-device resume
- no new runtime states
- no background polling or websocket orchestration

## Constraints

- preserve `session_runtime` as the source of truth for session state
- preserve the stable answer boundary once `/answer` succeeds
- keep draft transcript persistence UI-local only
- clear stale client state when backend session no longer exists

## Test contract

### 1. Awaiting answer restore

Given:
- local storage contains an active session envelope
- backend session state is `awaiting_answer`

Then:
- UI restores the prompt
- UI restores the draft transcript
- UI restores the profile selection from backend mode/intent

### 2. Evaluation pending restore

Given:
- local storage contains an active session envelope with `answerSubmitted=true`
- backend session state is `evaluation_pending`

Then:
- UI must not call `/answer` again
- UI must continue via evaluate/review recovery path
- review should render once available

### 3. Review presented restore

Given:
- local storage contains an active session envelope
- backend session state is `review_presented`

Then:
- UI loads the review artifact directly
- UI must not call `/answer` or `/evaluate`

### 4. Stale session cleanup

Given:
- local storage contains an active session envelope
- backend returns `404` for that session

Then:
- UI clears the stale envelope
- UI returns to the launcher surface

### 5. Reset cleanup

Given:
- UI has an active local session envelope

Then:
- explicit reset clears the local envelope

## Acceptance criteria

- reload preserves honest runtime semantics
- answer submission is never repeated after stable acceptance
- review can be recovered from `evaluation_pending` and `review_presented`
- stale client state does not leave the UI stuck
- frontend tests and production build pass

## Weak spots review

- draft transcript remains browser-local and may diverge from backend truth; the
  backend still owns only stable submission boundaries
- `evaluation_pending` is not a server-pushed async flow today, so recovery must
  continue through explicit client calls to existing endpoints
- if future scope requires cross-device resume or persisted drafts, that will
  need a new contract and likely a new slice

## Source-of-truth review

- `docs/00_change_protocol.md`: implementation-only change; ADR not required
- `docs/03_architecture/session_runtime_state_machine_v1.md`: preserved
- `docs/03_architecture/implementation_mapping_v1.md`: preserved
