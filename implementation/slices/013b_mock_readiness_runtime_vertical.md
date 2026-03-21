# Slice 013b: Mock Readiness Runtime Vertical

## Status

- planned

## Execution posture

`013b` starts only after `013a` lands a legal scenario-backed executable unit
for `MockInterview / ReadinessCheck`.

This slice is the narrow verticalization step for the first real mock path:
- one scenario family
- one bounded follow-up round
- deterministic runtime, evaluation, and recommendation behavior
- minimal UI needed to exercise the loop end-to-end

## Goal

Turn the seeded `URL Shortener` scenario-backed unit from `013a` into the first
honest user-visible `MockInterview / ReadinessCheck` path across:
- recommendation unlock
- runtime execution
- evaluation and review
- minimal launcher/session/review UI

The slice should ship a guided mini-mock, not a general mock-interview
framework.

## Affected bounded contexts

- `session_runtime`
- `evaluation_engine`
- `recommendation_engine`
- `web_api / ui`
- narrow consumption in `learner_projection`

## Non-goals

- no second scenario family
- no open-ended interviewer loop
- no dynamic follow-up generation
- no voice flow
- no persistence redesign
- no broader content-authoring framework changes
- no replacement of rubric-first evaluation with model-only judging

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- top-level modes remain `Study`, `Practice`, `MockInterview`
- recommendation still selects a structured learning action, not turn-by-turn
  orchestration
- mock support policy must be stricter than `Practice`
- follow-up behavior must be deterministic and capped at one round
- the first shipped path must remain scenario-family specific and auditable

## Hidden assumptions to lock before code

- `013a` provides exactly one legal executable unit family:
  `scenario_readiness_check`
- first runtime target remains `URL Shortener`
- one follow-up round is sufficient for the first shipped mini-mock
- readiness unlock should remain conservative and explainable
- review output may be richer than concept recall, but must stay bounded and
  deterministic

## Architectural approaches considered

### Option A: One narrow end-to-end mini-mock slice

- implement runtime, evaluator dispatch, recommendation unlock, and minimal UI
  together for one scenario family

Trade-offs:
- honest first user-visible value
- preserves end-to-end testability
- denser change set across several bounded contexts

### Option B: Split runtime/evaluator from recommendation/UI again

- first land runtime/evaluator, then recommendation and UI in another slice

Trade-offs:
- smaller diffs
- leaves the repo in an intermediate state without a real mock path
- weaker product validation

Decision:
- choose Option A

## Proposed implementation shape

### 1. Runtime posture

Add bounded runtime support for `unit_family = scenario_readiness_check`.

Expected posture:
- `mode = MockInterview`
- `session_intent = ReadinessCheck`
- deterministic prompt presentation
- at most one follow-up round
- stricter hint policy than `Practice`
- answer reveal remains unavailable
- closure and abandonment remain explicit and auditable

### 2. Evaluation and review posture

Dispatch evaluation using:
- `scenario_family = url_shortener`
- `evaluation_binding_id = binding.url_shortener.v1`

Expected review improvements over concept recall:
- multi-criterion strengths and misses
- scenario-specific next-step guidance
- explicit mention of follow-up handling when a follow-up round occurred
- closure outcome suitable for downstream learner/recommendation use

### 3. Recommendation posture

Expose one bounded mock action:
- `MockInterview / ReadinessCheck`
- `target_type = scenario_family`

Unlock rules:
- only when readiness estimate and confidence clear conservative thresholds
- suppressed when abandonment, fragility, or support dependence indicate a
  lower-pressure step is safer
- rationale must explain unlock or suppression

### 4. UI posture

Extend the current shell only as far as needed to:
- launch the mock path
- render the initial scenario prompt
- render one bounded follow-up
- show the richer mock review
- preserve reset/recovery semantics

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_session_runtime.py`
  Runtime behavior for mock start, support policy, follow-up cap, and closure.
- `backend/tests/test_recommendation_engine.py`
  Conservative mock unlock and suppression behavior.
- `backend/tests/test_smoke_backend_loop.py`
  Narrow end-to-end backend loop once the mock path exists.
- `frontend/src/App.test.tsx`
  Minimal launcher -> mock session -> review flow.

### Phase 1. Runtime

Lock tests that prove:
- mock session starts from the seeded scenario-backed unit
- answer reveal is rejected
- hint policy is stricter than `Practice`
- exactly one follow-up round is allowed
- a second follow-up attempt fails closed
- completion and abandonment remain aligned with the global state machine

### Phase 2. Evaluation and review

Lock tests that prove:
- mock unit dispatches to the scenario binding, not `concept_recall`
- review output includes bounded mock-specific next-step guidance
- follow-up presence changes review wording deterministically

### Phase 3. Recommendation

Lock tests that prove:
- weak or uncertain learners do not get mock recommendation
- sufficiently ready learners may get the bounded mock action
- recent abandonment or support dependence suppresses escalation

### Phase 4. UI

Lock tests that prove:
- launcher can start the mock path without adding a new pseudo-mode
- the shell renders the scenario prompt and one follow-up
- the review surface renders mock-specific summary fields
- reset/restore behavior remains coherent

## Acceptance criteria

- one real `MockInterview / ReadinessCheck` path works end-to-end for
  `URL Shortener`
- runtime support remains deterministic and bounded to one follow-up round
- evaluator dispatch and review are scenario-aware
- recommendation unlock remains conservative and explainable
- no second scenario family or open-ended interviewer framework is introduced

## Weak spots and undefined areas

- follow-up prompt selection must be deterministic; if selection policy remains
  ambiguous, it should be frozen in this slice before runtime code lands
- readiness thresholds must be explicit in tests, not implied by heuristics
- if current evaluator seams cannot honestly support the scenario binding,
  `013b` should stop and surface that blocker rather than fake coverage

## Source-of-truth review

Before implementation, review and sync as needed:
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`

Current expectation:
- no ADR should be required if `013b` remains a bounded realization of the
  existing mock mode and rubric-first posture

## Exit condition

`013b` is complete when the repository can exercise one conservative, bounded,
scenario-backed mock path end-to-end without violating the v2.2 baseline.
