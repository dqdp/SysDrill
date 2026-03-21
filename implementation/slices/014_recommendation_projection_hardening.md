# Slice 014: Recommendation And Projection Hardening

## Status

- implemented

## Execution posture

`014` is a narrow hardening slice over the current v2.2 implementation
baseline. It exists to close review-discovered correctness gaps in the current
`recommendation -> runtime -> learner_projection -> launcher shell` loop
without reopening the broader architecture.

Implementation posture:
- tests first
- no new bounded contexts
- no durable persistence redesign in this slice
- no broad UX redesign

## Goal

Close the highest-signal defects from review in four places:
- recommendation lifecycle linkage
- ordering semantics used by recommendation history and latest reviewed outcome
- wall-clock recency handling in learner projection
- stale recommendation recovery in the frontend shell

The slice also returns repository verification to green by fixing the new lint
failures introduced in the same change wave.

## Findings addressed

1. a single `decision_id` can currently be started multiple times and its
   acceptance/completion linkage is overwritten
2. anti-loop history is ordered by `decision_id`, not by actual acceptance time
3. latest reviewed outcome per concept is derived from `session_id`, not from
   actual reviewed time
4. `review_due_risk` recency is anchored to the latest event already present in
   the profile instead of wall-clock time
5. frontend stale recommendation recovery handles only `404`, leaving some
   stale `400` start failures unrecovered
6. CI is red because `ruff check` fails on newly added files

## Affected bounded contexts

- `recommendation_engine`
- `session_runtime`
- `learner_projection`
- `web_api / ui`
- narrow operational verification surfaces

## Non-goals

- no new persistence layer for decisions, sessions, or learner state
- no multi-device recommendation/session resume
- no expansion of the recommendation action space
- no new recommendation lifecycle event types
- no broad rewrite of the learner-state model
- no reopening of mode or bounded-context decisions

## Constraints

- preserve the v2.2 implementation baseline
- keep recommendation selecting a structured learning action, not a raw unit or
  turn-by-turn orchestration
- preserve append-only runtime events as the learner-evidence source
- keep learner projection unknown-biased and conservative
- keep frontend recovery explicit; it must not silently substitute a different
  action while pretending the cached one still launched

## Hidden assumptions to validate during implementation

- recommendation acceptance should remain one-to-one with a launched session in
  the current process-local implementation
- recommendation completion should remain tied to the accepted session, not any
  later arbitrary session using the same action shape
- "latest reviewed outcome" should mean latest by reviewed timestamp, not by
  session creation order
- review-due recency should be evaluated against wall clock even when the
  learner has no newer in-process events
- stale recommended-start failures can be identified deterministically from the
  current backend error surface without adding a new preflight endpoint

## Architectural approaches considered

### Option A: Local seam hardening inside the current process-local design

- keep the current in-memory recommendation/runtime stores
- enforce single-use recommendation acceptance/completion semantics inside the
  current backend seam
- derive ordering from actual acceptance/review timestamps
- anchor projection recency to wall clock through an injectable clock seam
- broaden frontend stale recovery using current error status/detail patterns

Trade-offs:
- minimal scope
- preserves current architecture and contracts
- fastest path to correctness and green verification
- keeps process-local limitations in place

### Option B: Broaden contracts around durable recommendation lifecycle

- add durable recommendation persistence, explicit start-validation, and richer
  public lifecycle metadata
- possibly expose reviewed timestamps and recommendation lifecycle state more
  broadly through public APIs

Trade-offs:
- cleaner long-term ownership
- stronger recovery semantics across restarts/devices
- much larger scope and higher doc/API sync cost
- not justified by the current defects

Decision:
- choose Option A

## Proposed implementation shape

### 1. Recommendation lifecycle hardening

Tighten recommendation start/completion semantics so a decision cannot be
accepted multiple times or completed against the wrong session.

Expected posture:
- first accepted session wins
- repeated accept attempts for the same `decision_id` fail closed
- completion requires a matching accepted session
- decision log linkage remains immutable once set

### 2. Ordering semantics hardening

Normalize ordering decisions around actual event times instead of generated ids.

Expected posture:
- anti-loop history uses `accepted_at`
- latest reviewed outcome uses the latest reviewed/evaluation timestamp
- fallback ordering only applies when timestamps are truly absent

### 3. Learner projection recency hardening

Use wall-clock time for recency-sensitive projection rules while keeping the
current rebuild-on-read projector posture.

Expected posture:
- projection accepts an injectable `now` seam for deterministic tests
- `review_due_risk` grows when evidence becomes old even without newer learner
  activity in memory
- unknown remains distinct from weak

### 4. Frontend stale recommendation recovery hardening

Broaden stale-start recovery so cached launcher state is discarded for all
backend responses that mean "this saved recommendation can no longer launch".

Expected posture:
- stale cached recommendation is cleared
- launcher remains visible
- UI fetches a fresh recommendation and shows an explicit message
- non-stale `400` failures still surface as normal errors

### 5. Verification hardening

Fix all current lint violations introduced by the reviewed commit range and
make the full local verification surface green again.

## TDD plan

### Phase 1. Lock recommendation lifecycle behavior

Add or update backend tests that prove:
- starting the same `decision_id` twice fails closed
- `mark_accepted` does not overwrite existing linkage
- `mark_completed` rejects completion before acceptance
- `mark_completed` rejects completion for a different session than the accepted
  one
- recommendation-backed API start returns a conflict-style failure on repeated
  launch

Only after those tests exist should backend lifecycle code change.

### Phase 2. Lock ordering behavior

Add or update tests that prove:
- `_recent_accepted_patterns()` orders by `accepted_at`
- latest reviewed concept outcome is selected by reviewed timestamp, not by
  `session_id`
- out-of-order completion/evaluation does not corrupt recommendation decisions

Only after those tests exist should runtime/recommendation ordering code change.

### Phase 3. Lock projection recency behavior

Add or update projector tests that prove:
- an old successful concept accrues materially higher `review_due_risk` when
  evaluated against a later wall-clock `now`
- repeated current-time recomputation remains deterministic under an injected
  clock
- sparse old evidence does not collapse into confirmed weakness just because it
  is old

Only after those tests exist should projector recency code change.

### Phase 4. Lock stale launcher recovery behavior

Add or update frontend tests that prove:
- cached recommendation recovery still works on `404`
- cached recommendation recovery also works on stale `400` failures that match
  known backend stale-start semantics
- ordinary `400` launch failures that are not stale do not silently refresh the
  recommendation

Only after those tests exist should frontend stale-detection code change.

### Phase 5. Lock verification surface

Add or update verification expectations so:
- `make ci-python` passes locally
- `make verify-frontend` still passes locally
- no new lint violations remain in touched files

## Test contract

### 1. Single-use recommendation acceptance

Given:
- a generated recommendation decision
- one successful recommended launch

Then:
- a second launch attempt with the same `decision_id` fails closed
- stored acceptance linkage remains unchanged

### 2. Completion must match the accepted session

Given:
- a decision accepted by session A

Then:
- only session A may mark the decision completed
- completion for session B fails closed

### 3. Recommendation history respects acceptance time

Given:
- multiple accepted decisions whose `decision_id` order differs from their
  acceptance order

Then:
- anti-loop history uses real acceptance order

### 4. Latest reviewed outcome respects reviewed time

Given:
- two reviewed outcomes for the same concept
- the later-reviewed session has the older `session_id`

Then:
- recommendation consumes the later-reviewed outcome

### 5. Review-due risk grows with wall-clock age

Given:
- a concept with only old reviewed evidence
- a later injected `now`

Then:
- `review_due_risk` increases relative to the earlier clock point
- the concept may become eligible for review-oriented recommendation

### 6. Frontend stale recommendation recovery remains explicit

Given:
- a cached recommendation in browser storage
- backend returns a stale-start error

Then:
- the cached recommendation is cleared
- a fresh recommendation is loaded
- the learner stays on the launcher with an explicit recovery message

### 7. Verification is green

Given:
- the slice implementation is complete

Then:
- `make ci-python` passes
- `make verify-frontend` passes

## Concrete implementation plan

1. Add failing backend tests for recommendation single-use acceptance and
   accepted-session-bound completion.
2. Harden `RecommendationEngine` and the recommendation-backed start endpoint to
   reject repeated acceptance/completion overwrites.
3. Add failing tests for recommendation history ordering and latest reviewed
   outcome ordering under out-of-order acceptance/evaluation.
4. Introduce timestamp-based ordering in runtime read seams and recommendation
   history consumption.
5. Add failing projector tests with an injected wall-clock seam for
   `review_due_risk`.
6. Update projector recency logic to use wall-clock `now` while preserving
   deterministic tests.
7. Add failing frontend tests for stale `400` recovery and non-stale `400`
   rejection.
8. Narrowly expand stale recommendation detection in the frontend shell.
9. Fix the current `ruff` line-length violations and rerun repository
   verification.
10. Sync source-of-truth docs only where implementation clarifies semantics
    that should become explicit.

## Acceptance criteria

- recommendation decisions are single-use for acceptance in the current
  process-local implementation
- decision acceptance/completion linkage is no longer overwritten
- anti-loop history reflects actual acceptance order
- latest reviewed outcome selection reflects actual reviewed order
- projection recency uses wall clock and can surface overdue review honestly
- stale cached recommendation recovery covers the current backend stale-start
  error surface without masking unrelated launch errors
- `make ci-python` and `make verify-frontend` pass

## Weak spots review

- single-use recommendation acceptance is a stronger behavioral stance than the
  current implementation; if product intent later requires resumable
  multi-launch decisions, this slice should stop before code and revisit the
  contract explicitly
- timestamp-based ordering must avoid relying on string sort unless all
  timestamps are normalized and parsed consistently
- wall-clock projection tests must use an injected clock seam; tests that read
  real time directly will become flaky
- frontend stale-error classification should match backend semantics narrowly by
  detail pattern and status, otherwise real user errors may be misclassified as
  stale cache

## Source-of-truth review

- `docs/00_change_protocol.md`: this slice is intended as contract-preserving
  hardening; ADR is not expected if implementation stays within the current
  bounded contexts and policy surface
- `docs/03_architecture/learner_state_update_rules_v1.md`: likely needs a small
  clarification that recency-sensitive review risk is anchored to wall clock,
  not only to newer in-memory learner events
- `docs/03_architecture/recommendation_policy_v1.md`: likely needs a small
  clarification that recent recommendation history should reflect actual
  acceptance order
- `docs/03_architecture/recommendation_engine_surface.md`: update only if the
  implementation makes acceptance/completion linkage semantics explicit in the
  stable decision envelope
- `docs/05_ops/recommendation_decision_logging_and_offline_evaluation.md`:
  likely needs clarification that acceptance/completion linkage is one-to-one
  in the current implementation wave

ADR requirement:
- not expected

Schema/example updates expected:
- none by default
- revisit only if public payloads or documented decision-log fields change

Baseline status:
- preserves the v2.2 implementation baseline
