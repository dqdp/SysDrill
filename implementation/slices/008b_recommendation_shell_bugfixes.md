# Slice 008b: Recommendation Shell Bugfixes

## Status

- in progress

## Goal

Fix three scoped regressions introduced by the recommendation/frontend shell work
without changing the v2.2 baseline, bounded-context ownership, or public
runtime/recommendation contracts.

## Affected bounded contexts

- `web_api / ui`
- `recommendation_engine`
- narrow `session_runtime` consumption semantics in the UI

## Non-goals

- no new backend endpoints
- no change to session state-machine semantics
- no recommendation policy redesign
- no production deployment/config refactor

## Constraints

- preserve existing `POST /runtime/sessions/{session_id}/evaluate` contract
- preserve existing `POST /recommendations/next` response shape
- keep manual launcher and recommendation flow both functional
- keep fixes minimal and deterministic

## Test contract

### 1. Evaluation retry path

Given:
- a session answer submission succeeds
- the first evaluate request fails transiently

Then:
- the UI must not try to submit the answer again on retry
- the learner must be able to trigger evaluation again and reach review

### 2. Recommendation dev proxy

Given:
- documented local frontend dev flow
- default empty `VITE_API_BASE_URL`

Then:
- `/recommendations/*` must be proxied to the backend alongside existing API
  paths

### 3. Filtered recommendation candidates

Given:
- recommendation guardrails remove a repeated action pattern

Then:
- `RecommendationDecision.candidate_actions` must expose only the post-filter
  candidate set that remains legal for the current decision
- blocked patterns must not still appear as selectable alternatives

## Planned test changes

- extend frontend app tests with a retry scenario where `/answer` succeeds,
  `/evaluate` fails once, and a second review request reaches review without a
  second `/answer`
- extend recommendation engine tests to assert `candidate_actions` excludes the
  anti-loop-blocked pattern
- keep the proxy fix covered by config inspection plus targeted verification

## Acceptance criteria

- frontend retry path recovers from transient evaluate failure
- local Vite dev server proxies recommendation requests
- recommendation payload is internally consistent with applied guardrails
- targeted frontend and backend tests pass

## Weak spots review

- the UI currently has no explicit persisted “evaluation pending” phase, so the
  fix should derive retry behavior from local state only and avoid inventing a
  new backend contract
- Vite proxy behavior is not naturally unit-tested here, so verification must
  include direct config inspection
- recommendation candidate filtering must preserve chosen action validity and
  must not alter ranking behavior beyond removing blocked alternatives

## Source-of-truth review

- `docs/00_change_protocol.md`: change is implementation-only; ADR not required
- `docs/03_architecture/session_runtime_state_machine_v1.md`: preserved
- `docs/03_architecture/recommendation_engine_surface.md`: preserved and
  tightened in implementation
- `docs/03_architecture/implementation_mapping_v1.md`: preserved
