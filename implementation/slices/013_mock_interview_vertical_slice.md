# Slice 013: Mock Interview Vertical Slice

## Status

- completed

Execution is now split across:
- `013a_url_shortener_scenario_seed.md`
- `013b_mock_readiness_runtime_vertical.md`
- `013c_mock_outcome_projection_feedback.md`

Status of child slices:
- `013a` completed
- `013b` completed
- `013c` completed

## Execution posture

`013` started as conditional on executable mock content readiness. That blocker
has now been removed by `013a`, and the first bounded mock runtime path has
been implemented in `013b`.

Current repository posture:
- one bounded `MockInterview / ReadinessCheck` scenario-family path exists for
  `URL Shortener`
- runtime, evaluation, recommendation unlock, and minimal UI are already
  verticalized for that path
- the remaining open item is downstream feedback from mock outcomes into
  learner projection and later recommendation behavior, now isolated as `013c`

## Goal

Deliver the first real mock-oriented progression step on top of the existing
`recommendation -> runtime -> evaluation -> learner_projection` loop, while
keeping the slice narrow enough to ship as a guided or mini-mock rather than a
full interviewer simulation.

This slice exists to convert the internal readiness and recommendation work from
`009`-`012` into a user-visible progression step that feels:
- gated rather than always available
- stricter than `Study` and `Practice`
- auditable through the same runtime/evaluation/review seams as the rest of v1

## Affected bounded contexts

- `recommendation_engine`
- `session_runtime`
- `evaluation_engine`
- `learning_design`
- `web_api / ui`
- narrow consumption in `learner_projection`

## Non-goals

- no voice-first experience
- no full interviewer simulation
- no unrestricted scenario graph
- no broad content-authoring redesign
- no polished end-state mock UX beyond one bounded slice
- no attempt to cover every system-design domain in the first mock pass

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- top-level modes remain only `Study`, `Practice`, and `MockInterview`
- recommendation still selects a structured learning action, not turn-by-turn
  orchestration
- rubric-first hybrid evaluation remains in place
- mock gating must remain conservative and grounded in available evidence
- the first slice must fit the currently available content/runtime posture

## Known starting point

- `009` introduced conservative `mock_readiness_estimate` and
  `mock_readiness_confidence`
- `010` made recommendation consume learner projection internally
- `011` and `012` are intended to enrich runtime events and expose learner
  summary surfaces before mock work is implemented
- current runtime/evaluation path is still concept-recall oriented and does not
  yet support a broad multi-turn interview experience
- current recommendation action space is still bounded by implemented learning
  unit families

## Architectural approaches considered

### Option A: Guided mini-mock vertical slice

- implement a bounded `MockInterview` path as a `ReadinessCheck` intent over one
  narrow scenario family
- use a stricter runtime posture and richer review than `Practice`
- keep the number of turns and content variants tightly bounded

Trade-offs:
- best fit for first shipped value
- allows real gating and richer review without pretending full interview depth
- lower authoring and runtime complexity
- not yet representative of a full mock interview experience

### Option B: Full mock-interview framework first

- implement broader multi-turn scenario orchestration, richer follow-ups, and a
  more complete interviewer loop immediately

Trade-offs:
- closer to the eventual product vision
- much higher scope and execution risk
- likely blocked by content/rubric/runtime maturity

### Option C: Recommendation-only mock placeholder

- recommend mock actions without a distinct runtime/evaluation path

Trade-offs:
- smallest effort
- low product honesty
- does not create a true new progression step

Decision:
- choose Option A

## Proposed implementation shape

### Chosen first form factor

`013` should lock one concrete first form factor rather than leaving mock shape
ambiguous.

Chosen posture:
- `mode = MockInterview`
- `session_intent = ReadinessCheck`
- `target_type = scenario_family`
- one bounded scenario family for the first shipped slice
- short session size
- at most one follow-up round

Rules:
- `013` should not introduce a separate pseudo-mode or a practice-flavored
  readiness check outside `MockInterview`
- recommendation may still choose not to surface this action when readiness
  evidence is insufficient
- if content/runtime constraints force a different form factor, the slice doc
  must be revised before implementation

### Content and authoring preconditions

`013` should be considered implementation-ready only if the following
preconditions are met:
- at least one executable scenario family is materializable by the current
  `learning_design` stack for `MockInterview`
- an explicit scenario-rubric binding exists for that family
- rubric criteria cover the bounded mock concerns the review will talk about
- a deterministic follow-up envelope is defined for the chosen family
- review rendering has a bounded template for strengths, misses, and next-step
  guidance
- test fixtures exist for the chosen scenario family and rubric binding

### Recommendation gate

Add a bounded recommendation path for mock-like work:
- the chosen `MockInterview / ReadinessCheck` action
- only surfaced when learner readiness evidence clears a conservative threshold

Rules:
- low-confidence readiness must not unlock mock by default
- repeated abandonment or strong weakness may suppress or delay mock escalation
- recommendation rationale should explain why mock is or is not being suggested

### Learning-design and content envelope

Use a bounded scenario family rather than arbitrary mock composition.

Recommended first slice posture:
- exactly one narrow scenario family
- explicit scenario-rubric binding
- bounded prompt/follow-up envelope with at most one follow-up round

Rules:
- content should be executable by the current learning-design/runtime stack
- do not require a new authoring model for the first slice
- if the content preconditions above are not met, implementation should stop
  and backfill content/binding readiness before broadening runtime code

### Runtime posture

Extend runtime only as far as needed for a mini-mock:
- stricter hint policy than `Practice`
- bounded follow-up pressure
- explicit closure and abandonment handling

Rules:
- follow-up count and closure policy should be deterministic
- mock-specific runtime should still respect the global state-machine contract
- the first shipped path should cap follow-up breadth rather than expose an
  open-ended interviewer loop

### Evaluation and review posture

Provide a richer review artifact than current concept-recall drills while
remaining rubric-first.

Expected review improvements:
- stronger articulation of strengths and misses across the bounded mock unit
- clearer readiness signal or next-step guidance after the mock
- explicit mention of follow-up handling if a follow-up round occurred

Rules:
- do not replace rubric-first scoring with free-form model-only judging
- evaluation remains auditable and separable from runtime interaction facts
- "richer than concept-recall baseline" in `013` means at least:
  - multi-criterion strengths/misses summary for the bounded scenario
  - mock-specific next-step guidance
  - explicit closure outcome suitable for downstream learner and recommendation
    loops

## Policy scope for 013

### Unlock behavior

Mock should only become recommendable when:
- concept/subskill evidence is strong enough
- mock-readiness confidence is sufficient
- recent abandonment/support signals do not indicate the learner still needs a
  lower-pressure step

### Block behavior

Mock should remain blocked or deprioritized when:
- readiness evidence is insufficient
- repeated recent abandonment indicates unstable trajectory
- support dependence remains too high for a stricter mode

### Post-mock outcome handling

Mock results should feed back into:
- learner projection
- future recommendation bias
- learner-facing review and summary surfaces

## Test contract

### 1. Readiness gate blocks weak or uncertain learners

Given:
- low readiness estimate or low readiness confidence

Then:
- recommendation does not surface the mock action
- rationale explains that more evidence or lower-pressure practice is needed

### 2. Readiness gate unlocks mock conservatively

Given:
- sufficiently strong concept/subskill evidence with adequate readiness
  confidence

Then:
- recommendation may surface the bounded `MockInterview / ReadinessCheck`
  action
- gating remains deterministic and test-covered

### 3. Mock runtime enforces stricter support policy

Given:
- an active mini-mock session

Then:
- hint/reveal behavior follows stricter policy than `Practice`
- runtime remains deterministic about allowed support actions

### 4. Mock session emits follow-up and closure events

Given:
- a learner completes the bounded mini-mock flow

Then:
- runtime emits the expected follow-up and closure events
- follow-up count does not exceed the documented bounded envelope
- session reaches stable reviewed completion or deterministic abandonment

### 5. Mock review is richer than concept-recall review

Given:
- a completed mock-like session

Then:
- review output contains richer cross-criterion guidance than the current basic
  concept-recall path
- review remains compatible with rubric-first evaluation posture

### 6. Mock outcomes feed back into learner and recommendation loops

Given:
- a completed or abandoned mock-like session

Then:
- learner projection updates appropriately
- later recommendation decisions reflect the mock outcome without changing the
  public API shape

### 7. Content preconditions are real, not implied

Given:
- the chosen scenario family lacks executable materialization, binding, or
  review-template support

Then:
- `013` is not implementation-ready
- the team backfills content prerequisites instead of widening the runtime slice

## Acceptance criteria

- recommendation can conservatively unlock a bounded mock-like action
- that action is concretely `MockInterview / ReadinessCheck` over one bounded
  scenario family
- runtime can execute a guided mini-mock path with deterministic closure
- evaluation/review for that path is richer than the concept-recall baseline
- learner projection and later recommendations consume mock outcomes
- the slice ships a real progression step without claiming full interview
  simulation breadth

## Weak spots review

- content readiness is the biggest delivery risk; a vertical slice can stall if
  suitable scenario/rubric bindings do not exist
- mock gating can feel arbitrary unless `012` summary/rationale surfaces already
  explain readiness clearly
- follow-up breadth can explode scope quickly if the runtime envelope is not
  tightly bounded
- stricter support policy may expose UX rough edges in the current shell
- if the exact first form factor is not locked, implementation may drift into a
  hybrid `Practice`/`MockInterview` design that violates the modes model

## Hidden assumptions called out

- a guided mini-mock is an acceptable first product instantiation of
  `MockInterview`
- `011` and `012` land first or equivalent capabilities exist by the time `013`
  is implemented
- existing content/rubric authoring posture can support at least one bounded
  mock-like scenario family without a parallel content redesign
- a single scenario-family-first slice is preferable to a shallower
  multi-family mock placeholder

## Source-of-truth review

- `docs/00_change_protocol.md`: recommendation, runtime, learner, and
  evaluation sync sets all matter for this slice
- `docs/03_architecture/recommendation_policy_v1.md`: gating and next-step
  posture
- `docs/03_architecture/session_runtime_state_machine_v1.md`: mock runtime must
  remain within the documented state machine
- `docs/03_architecture/interaction_event_model.md`: follow-up/support/closure
  events must stay semantic and auditable
- `docs/03_architecture/evaluation_engine_v1.md`: rubric-first evaluation
  posture must be preserved
- `docs/03_architecture/scenario_rubric_binding_v1.md`: scenario/rubric binding
  remains load-bearing
- `docs/03_architecture/implementation_mapping_v1.md`: ownership boundaries
  across recommendation/runtime/evaluation/learner remain explicit

## Change protocol expectations

- an ADR is not automatically required if `013` stays within the existing
  `MockInterview` mode and existing ownership boundaries
- source-of-truth doc updates are likely if the first shipped mock slice forces
  clarifications to follow-up limits, support policy, or review semantics
- v2.2 baseline should remain preserved if the slice stays additive and bounded
