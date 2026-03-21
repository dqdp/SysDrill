# Slice 015b: Review-Time Recency Hardening

## Status

- completed

## Execution posture

`015b` is a narrow hardening follow-up after completed `015a`.

Purpose:
- correct the remaining recency bug where learner evidence timestamps are still
  anchored to the latest session event instead of the review/evaluation moment
- keep the fix local to learner projection unless a narrower seam proves
  impossible
- preserve the conservative v2.2 learner-state posture

This slice is about timestamp semantics, not new recommendation policy.

## Goal

Ensure concept and subskill recency are anchored to reviewed evidence time,
while trajectory activity remains anchored to latest user activity.

Expected outcome:
- `last_evidence_at` for reviewed knowledge evidence no longer shifts forward
  on late `session_completed`
- `review_due_risk` grows from actual review/evaluation time, not from closure
  latency
- `last_active_at` still reflects the latest session event
- no public API shape changes are required

## Why this slice exists

Post-`015a` review still leaves one correctness gap:
- learner projection rebuilds concept/subskill evidence from the latest session
  event timestamp
- if a learner waits on the review screen and completes later, the later
  `session_completed` event refreshes concept recency incorrectly
- this conflicts with
  [learner_state_update_rules_v1.md](/Users/alex/SysDrill/docs/03_architecture/learner_state_update_rules_v1.md),
  which says recency-sensitive updates should compare against current evaluation
  time, not merely against the newest event in the rebuilt profile

This is orthogonal to:
- `015a` bound-concept rollback
- `015c` recommendation-start idempotency
- deferred `016` concept-specific mock feedback

## Affected bounded contexts

- `learner_projection`
- read-only event consumption from `session_runtime`

## Non-goals

- no recommendation-start retry changes
- no frontend/UI changes
- no new evaluator contract
- no event-schema redesign
- no change to `last_active_at` semantics
- no attempt to revise concept/subskill weighting

## Constraints

- preserve v2.2 baseline
- keep `evaluation_attached` as the primary proficiency update event
- keep learner-state rebuild deterministic
- do not reinterpret `session_completed` as direct knowledge evidence
- avoid broadening runtime or API surface unless strictly needed

## Hidden assumptions to lock before code

- reviewed sessions should anchor knowledge recency to semantic interpretation
  events, not lifecycle closure events
- `evaluation_attached` is the preferred timestamp when present
- `review_presented` is an acceptable fallback because it is still part of the
  same reviewed attempt boundary
- `session_completed` should continue to influence trajectory/activity, not
  concept recency
- some legacy or synthetic fixtures may contain `last_evaluation_result`
  without full semantic event history, so a conservative fallback path may still
  be needed

## Corrective options

### Option A: Projection-owned reviewed-evidence timestamp selection

Shape:
- add a local helper in `learner_projection` that derives reviewed evidence time
  from session events
- prefer `evaluation_attached`
- fall back to `review_presented`
- only if both are absent but `last_evaluation_result` exists, fall back to the
  latest session event to keep degraded histories deterministic

Pros:
- smallest possible change set
- no public/runtime interface changes
- keeps the bug fix inside the bounded context that currently misinterprets the
  events

Cons:
- projection owns one more piece of event-selection logic
- there is still a light duplication of review timestamp semantics relative to
  `SessionRuntime.list_user_reviewed_outcomes()`

### Option B: Runtime exports canonical reviewed-evidence timestamp

Shape:
- add a dedicated runtime seam for “reviewed evidence at”
- projection consumes that seam instead of re-reading events directly

Pros:
- single source of truth for reviewed timestamp semantics
- less duplication over time

Cons:
- broader scope
- changes runtime reader contract for a local hardening issue
- higher risk of incidental churn in tests and interfaces

## Recommendation

Choose Option A.

Reasoning:
- the bug lives in projection-time interpretation, not in runtime event
  emission
- current source-of-truth docs already support the fix; no contract expansion is
  needed
- this keeps `015b` clearly separated from the later idempotency and
  concept-specific feedback slices

## Proposed implementation shape

### 1. Split activity time from evidence time

Behavior:
- `latest_activity_at` remains derived from the latest session event
- concept/subskill evidence for reviewed sessions uses reviewed evidence time,
  not generic latest session time

Rules:
- trajectory `last_active_at` must remain unchanged
- concept/subskill `last_evidence_at` must stop drifting forward on late
  completion

### 2. Prefer semantic interpretation events for reviewed evidence

Behavior:
- choose `evaluation_attached` timestamp first
- if absent, choose `review_presented`
- if both are absent but the session still has `last_evaluation_result`, fall
  back to the latest session event as a degraded compatibility path

Rules:
- the fallback exists only to keep synthetic or legacy histories rebuildable
- normal runtime-produced reviewed sessions should hit the semantic-event path

### 3. Apply the same reviewed timestamp to concept and subskill evidence

Behavior:
- concept evidence and subskill evidence derived from one reviewed session share
  the same `evidence_at`
- late `session_completed` no longer refreshes either surface

Rules:
- do not change weighting logic in this slice
- do not change abandonment/activity handling in this slice

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_learner_projection.py`
  locks the recency contract for reviewed sessions, delayed completion, mock
  reviewed sessions, and degraded fallback when semantic review events are
  absent

### Phase 1. Reviewed timestamp selection

Lock tests that prove:
- a reviewed session with later `session_completed` keeps concept
  `last_evidence_at` at `evaluation_attached`/`review_presented`, not completion
  time
- subskill `last_evidence_at` behaves the same way

### Phase 2. Review-due behavior

Lock tests that prove:
- `review_due_risk` grows from time since reviewed evidence, not from time since
  later closure
- the wall-clock `now` seam still works on top of the corrected evidence time

### Phase 3. Mock and degraded history coverage

Lock tests that prove:
- reviewed mock sessions still update subskills/trajectory while using reviewed
  evidence time semantics
- if a synthetic reviewed fixture has `last_evaluation_result` but lacks
  `evaluation_attached` and `review_presented`, projection still rebuilds
  deterministically via fallback

## Acceptance criteria

- no reviewed concept/subskill evidence is refreshed solely by late
  `session_completed`
- `review_due_risk` reflects actual review/evaluation time plus wall-clock age
- trajectory `last_active_at` remains based on latest activity
- no API shape change is required
- `make ci-python` passes

## Exit criteria

- the bug from the review finding is covered by regression tests
- the fix remains local to `learner_projection` unless implementation proves a
  runtime seam is strictly necessary
- the branch is ready for the separate `015c` idempotency hardening slice
