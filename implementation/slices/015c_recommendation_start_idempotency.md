# Slice 015c: Recommendation Start Idempotency

## Status

- completed

## Execution posture

`015c` is a narrow hardening follow-up after completed `015b`.

Purpose:
- remove the dead-state retry gap on
  `/runtime/sessions/start-from-recommendation`
- make repeated identical starts idempotent within the current process-local
  baseline
- keep recommendation lifecycle single-use while allowing safe recovery from a
  lost start response

This slice is about recovery semantics, not new recommendation policy.

## Goal

Allow a repeated identical `start-from-recommendation` request to return the
already accepted session instead of failing with `409 decision is already
accepted`.

Expected outcome:
- a lost first response no longer strands the launcher on a stale cached
  recommendation
- recommendation acceptance remains single-use and still maps to exactly one
  session
- frontend can route the returned session by actual runtime state instead of
  assuming a fresh pre-answer start
- no new public endpoint is required

## Why this slice exists

Post-`015b` review still leaves one operability gap:
- `/runtime/sessions/start-from-recommendation` currently returns `409` when
  the same `decision_id` is replayed
- if the first start succeeded server-side but the client lost the response, a
  retry hits `already accepted`
- the current frontend only treats stale `400/404` recommendation starts as
  recoverable, so this path leaves the user in a dead launcher state

This is orthogonal to:
- `015a` bound-concept rollback
- `015b` review-time recency hardening
- deferred `016` concept-specific mock feedback

## Affected bounded contexts

- `recommendation_engine`
- `web_api`
- `web_ui`
- read-only runtime session lookup in `session_runtime`

## Non-goals

- no new recommendation ranking or policy changes
- no session persistence redesign across process restart
- no new resume token or client-generated idempotency key
- no broad frontend session-restore redesign beyond the returned start payload
- no change to single-use acceptance semantics

## Constraints

- preserve v2.2 baseline
- keep one `decision_id -> accepted_session_id` mapping
- do not allow replay to spawn a second session
- avoid adding a new endpoint if the existing surface can absorb the fix
- keep mismatched user/action requests fail-closed

## Hidden assumptions to lock before code

- `decision_id` already serves as the idempotency key for recommendation start
- idempotent replay is only expected within the current in-memory process; after
  restart, unknown decisions may still fail closed
- repeated identical start requests must not emit a second
  `recommendation_accepted` event
- the frontend cannot safely assume that a reused accepted session is still in
  `awaiting_answer`; it must route by returned session state

## Corrective options

### Option A: Backend-first idempotent replay on the existing endpoint

Shape:
- change recommendation acceptance flow so repeated identical start requests
  return the already accepted session snapshot
- keep validation strict for wrong user, wrong action, or missing accepted
  session
- on the frontend, route the returned session by actual state using existing
  recovery seams

Pros:
- single round trip for retry recovery
- no error-string heuristics for the happy recovery path
- keeps the idempotency key aligned with the existing recommendation lifecycle

Cons:
- requires a minimal frontend routing upgrade on successful start
- recommendation engine needs a slightly richer acceptance helper

### Option B: Keep `409`, but return structured recovery metadata

Shape:
- preserve conflict status for reused starts
- include `accepted_session_id` or structured error code
- frontend performs an additional fetch and recovery step

Pros:
- keeps lifecycle conflict explicit at the HTTP layer
- recommendation engine changes are smaller

Cons:
- still turns recovery into an error path
- requires more frontend branching and extra network round trips
- easier to regress back into dead-state handling

## Recommendation

Choose Option A.

Reasoning:
- the failure mode is operational, not semantic; the best fix is to make the
  existing start request safely replayable
- the decision remains single-use because replay returns the same session, not a
  new one
- this minimizes frontend heuristics and keeps the recovery path deterministic

## Proposed implementation shape

### 1. Make recommendation acceptance replay-safe

Behavior:
- first identical start request accepts the decision and creates the session
- later identical start requests return the already accepted session snapshot
- no second session is created

Rules:
- `mark_accepted()` may stay strict
- the acceptance path used by the start endpoint becomes idempotent through a
  dedicated helper in `recommendation_engine`, not through ad hoc orchestration
  in `app.py`
- if a decision is accepted but its session cannot be loaded, fail closed with a
  lifecycle error
- replay returns the canonical accepted session even if it is already in
  `review_presented`, `completed`, or `abandoned`; frontend must route by the
  returned state instead of assuming a fresh start

### 2. Keep validation fail-closed for non-identical retries

Behavior:
- wrong `user_id` still returns `400`
- mismatched `action` still returns `400`
- unknown decision still returns `404`

Rules:
- idempotency applies only to the same decision and same stored chosen action
- this slice must not weaken stale/mismatch validation

### 3. Route successful start responses by actual session state

Behavior:
- if the returned session is pre-answer, frontend enters the session phase
- if the returned session needs review recovery, frontend uses the existing
  review-loading seam
- if the returned session is already `review_presented`, frontend loads the
  review directly
- if the returned session is `completed` or `abandoned`, frontend clears the
  cached recommendation/session resume state and returns cleanly to launcher

Rules:
- do not duplicate bespoke recovery logic if existing session-restore helpers
  can be reused
- the launcher must not assume that a successful start response always means a
  brand-new session

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_recommendation_engine.py`
  repeated acceptance through the idempotent helper returns the original session
  instead of creating or accepting a second one
- `backend/tests/test_session_runtime.py`
  endpoint-level repeated start returns the same session snapshot and does not
  emit duplicate acceptance
- `frontend/src/App.test.tsx`
  retrying a recommended start after a lost first response recovers via success,
  not stale refresh or dead-state error

### Phase 1. Engine-level idempotency

Lock tests that prove:
- first acceptance creates and records one accepted session
- repeated identical acceptance returns that same session
- repeated replay does not call the session starter twice
- `mark_accepted()` remains non-idempotent and still rejects second acceptance

### Phase 2. Endpoint behavior

Lock tests that prove:
- second POST to `/runtime/sessions/start-from-recommendation` returns `200`
  with the same `session_id`
- only one `recommendation_accepted` event exists for that decision
- wrong-user and mismatched-action requests still fail as before

### Phase 3. Frontend recovery

Lock tests that prove:
- retrying the recommended start after a lost response resumes the session
  without fetching a fresh recommendation
- if the replayed accepted session is already in a review-bearing state,
  frontend routes to review recovery instead of blindly entering session mode
- if the replayed accepted session is already terminal, frontend returns to the
  launcher instead of entering a dead state

## Acceptance criteria

- repeated identical recommendation starts are idempotent within one process
- no second accepted session is created for the same decision
- no duplicate `recommendation_accepted` event is emitted
- frontend no longer dead-ends on the lost-response retry path
- `make ci-python` passes
- `make verify-frontend` passes

## Exit criteria

- the `409 already accepted` retry gap is covered by regression tests
- lifecycle semantics stay single-use and one-to-one
- the slice does not broaden beyond idempotent replay and minimal UI routing
