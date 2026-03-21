# Slice 009: Learner Projection Bootstrap

## Status

- completed

## Goal

Introduce the first narrow `learner_projection` implementation so the backend
can derive a deterministic learner profile from existing runtime/evaluation
facts without collapsing bounded contexts.

This slice exists to close the current gap between:
- append-only semantic interaction facts in `session_runtime`
- rule-first evaluation outputs in `evaluation_engine`
- future recommendation context that must consume learner state rather than raw
  reviewed outcomes

## Affected bounded contexts

- `learner_projection`
- narrow consumption of `session_runtime`
- narrow consumption of `evaluation_engine`

## Non-goals

- no recommendation policy or ranking changes
- no learner dashboard API yet
- no frontend changes
- no async worker or event-streaming infrastructure
- no durable cross-process persistence beyond the current monolith posture
- no direct mutation of learner state inside `session_runtime` or
  `evaluation_engine`
- no attempt to fully observe every v1 subskill when the current evaluator does
  not emit enough evidence

## Constraints

- preserve v2.2 baseline and current bounded-context seams
- `evaluation_attached` remains the primary proficiency update event
- insufficient evidence must remain distinct from confirmed weakness
- learner state remains `proficiency_estimate + confidence`, not mastery
- projector logic must be deterministic, interpretable, and rebuildable
- projector inputs must come from existing runtime session/event/evaluation
  facts; this slice should not revise event contracts
- current implementation may remain process-local while contracts stay explicit

## Known starting point

- there is currently no dedicated `learner_projection` module in `backend/`
- `session_runtime` already stores per-session events and reviewed outcomes
- current runtime-emitted event families available to the projector today are:
  - `session_planned`
  - `session_started`
  - `unit_presented`
  - `answer_submitted`
  - `evaluation_attached`
  - `review_presented`
  - `recommendation_accepted`
  - `recommendation_completed`
- current runtime does **not** yet emit projector-relevant events for:
  - `session_completed`
  - `session_abandoned`
  - `hint_requested`
  - `answer_revealed`
  - `follow_up_presented`
  - `follow_up_answered`
- `last_evaluation_result` already contains richer data than the emitted
  `evaluation_attached` event payload, including:
  - `criterion_results`
  - `downstream_signals`
  - `binding_id`
  - `weighted_score`
  - `overall_confidence`
- current evaluator primarily covers concept-recall evidence, not full mock or
  follow-up richness

## Projection input contract

`009` should make the projector consume explicit runtime-owned read seams rather
than private in-memory fields.

Required internal read inputs:
- a user-scoped iterable of session snapshots for `user_id`
- per-session semantic events
- stored `last_evaluation_result` when present

Recommended narrow runtime seam for this slice:
- add an internal read method such as
  `SessionRuntime.list_user_sessions(user_id: str) -> list[dict[str, Any]]`
- returned session snapshots should be deep-copied and include, at minimum:
  - `session_id`
  - `user_id`
  - `mode`
  - `session_intent`
  - `state`
  - `current_unit`
  - `source`
  - `event_ids`
  - `last_evaluation_result`
  - `last_review_report`
  - `recommendation_decision_id`

Rules:
- the projector may call `list_session_events(session_id)` for semantic facts
- the projector must not read `SessionRuntime._sessions` or other private
  runtime internals directly
- the projector must tolerate sparse event families and derive only what is
  actually supported by the current runtime history

## Architectural approaches considered

### Option A: Rebuild-on-read projector

- implement a dedicated `learner_projection` module family
- build a learner profile for one `user_id` by deterministically replaying
  current runtime session snapshots, event history, and stored evaluation
  results
- keep projection pure/idempotent for a given in-memory history
- do not introduce a public API in this slice; recommendation can consume the
  projector internally later

Trade-offs:
- best fit for correctness and bounded scope
- naturally idempotent and easy to test
- avoids double-apply/order bugs from incremental mutation
- acceptable while user history is still small and process-local
- read cost scales with per-user session history

### Option B: Incremental materialized projection store

- maintain a mutable learner profile snapshot and update it as events and
  evaluations arrive

Trade-offs:
- closer to a future production shape
- lower read latency
- significantly more complexity around ordering, replay, idempotence, and
  locking
- too broad for the first learner-projection slice

### Option C: Runtime-owned learner fields

- let `session_runtime` update learner state directly while it processes
  submissions/evaluations

Trade-offs:
- smallest code footprint in the short term
- violates bounded-context ownership and anti-collapse rules
- couples runtime orchestration to learner interpretation

Decision:
- choose Option A

## Initial projection scope

### 1. Concept state

For concept-targeted reviewed sessions, project:
- `proficiency_estimate`
- `confidence`
- `review_due_risk`
- `hint_dependency_signal`
- `last_evidence_at`

Initial scope note:
- bootstrap only concept-targeted units already materialized by the current
  runtime/evaluator path
- use session/content metadata already available from reviewed outcomes and
  session snapshots

### 2. Subskill state

Bootstrap only subskills that the current evaluator can support with clear,
non-ambiguous evidence:
- `tradeoff_reasoning`
- `communication_clarity`

Rules:
- do not fabricate values for unobserved subskills
- leave unsupported subskills absent/unknown for now rather than defaulting them
  to low proficiency

### 3. Trajectory state

Project:
- `recent_fatigue_signal`
- `recent_abandonment_signal`
- `mock_readiness_estimate`
- `mock_readiness_confidence`
- `last_active_at`

Bootstrap stance:
- `recent_fatigue_signal` and `recent_abandonment_signal` remain explicit
  zero-baseline fields in `009` because current runtime does not yet emit
  abandonment/fatigue-producing events
- `mock_readiness_*` remains conservative and low-confidence because current
  evidence is still concept-recall heavy and lacks real follow-up/mock signals

## Projection output contract

The `009` projector output should align structurally with
[/Users/alex/SysDrill/examples/schemas/learner-profile.example.yaml](/Users/alex/SysDrill/examples/schemas/learner-profile.example.yaml)
where the binding docs already define semantics, while explicitly deferring
fields that are not yet source-of-truth-defined.

Required top-level fields:
- `user_id`
- `concept_state`
- `subskill_state`
- `trajectory_state`
- `last_updated_at`

Keying rules:
- `concept_state` keys should use canonical `content_id` values such as
  `concept.alpha-topic`, not display titles or localized labels
- `subskill_state` keys should use the v1 canonical subskill identifiers from
  `learner_state_update_rules_v1.md`

Field rules:
- all numeric fields must be clamped to `[0.0, 1.0]`
- `last_updated_at` and all `last_evidence_at` values must be ISO-8601 UTC
  timestamps
- unsupported subskills remain absent from `subskill_state`; they are not
  emitted as synthetic zeroes
- `trajectory_state.recent_fatigue_signal` and
  `trajectory_state.recent_abandonment_signal` are present with bootstrap value
  `0.0` in `009`

Explicit deferral:
- `current_stage` appears in the example learner profile, but no binding source
  of truth currently defines how it should be updated
- `009` should therefore omit `current_stage` from the projector output unless a
  source-of-truth clarification is added before implementation

## Rule posture for 009

### Primary evidence

- reviewed sessions with `last_evaluation_result` are the primary concept and
  subskill evidence
- session events modulate evidence strength and trajectory state

### Evidence weighting

- `Study` updates concept familiarity more than applied readiness
- `Practice` weights applied confidence/subskills more than `Study`
- `MockInterview` weighting remains defined by docs but may be mostly dormant
  until mock slices land

### Support dependence

- `hint_requested` dampens positive evidence and increases dependency signals
- `answer_revealed` is a stronger dependency signal than hint use
- support use must reduce confidence growth more than raw proficiency

### Confidence growth

- repeated completed reviewed evidence grows confidence
- single strong performance must not overstate certainty
- sparse evidence must stay distinct from confirmed weakness

### Quantitative invariants

Implementation formulas may evolve, but `009` must lock the following testable
ordering and clamp rules:
- every projected numeric field is clamped to `[0.0, 1.0]`
- for otherwise equivalent evidence, an independent positive reviewed attempt
  must update confidence/proficiency at least as strongly as a hinted attempt
- for otherwise equivalent evidence, a hinted positive reviewed attempt must
  update confidence/proficiency at least as strongly as a reveal-dependent
  attempt
- repeated consistent positive reviewed outcomes must not decrease confidence
  for the same concept/subskill
- for otherwise equivalent evidence, supported subskill deltas in `Practice`
  must be greater than supported subskill deltas in `Study`
- without mock/follow-up evidence, `mock_readiness_confidence` must remain
  conservative and lower than strong concept-confidence cases

### Review-due risk

- driven by recency plus fragility and support dependence
- not driven by elapsed time alone

### Trajectory signals

- `last_active_at` is driven by the latest known session/evidence timestamp
- with the current emitted-event boundary, `recent_fatigue_signal` and
  `recent_abandonment_signal` remain zero-baseline rather than inferred from
  unrelated runtime states
- `mock_readiness_*` should move only conservatively in `009`

## Test contract

### 1. Empty/insufficient evidence

Given:
- a user with no reviewed outcomes

Then:
- the projected profile is empty or unknown-biased
- no concept/subskill is inferred as weak by default

### 2. Single reviewed Study outcome

Given:
- one completed `Study` concept-recall session with an attached evaluation

Then:
- the bound concept receives a modest `proficiency_estimate`
- `confidence` remains limited
- `last_evidence_at` is populated

### 3. Repeated reviewed outcomes

Given:
- multiple reviewed outcomes for the same concept across time

Then:
- `confidence` grows more than from a single strong attempt
- `proficiency_estimate` changes smoothly rather than jumping to certainty

### 4. Hint and reveal damping

Given:
- otherwise similar reviewed sessions with and without support use

Then:
- support-dependent sessions raise `hint_dependency_signal`
- positive proficiency updates are damped
- reveal usage dampens more strongly than hint-only usage

### 5. Mode weighting

Given:
- comparable reviewed evidence in `Study` and `Practice`

Then:
- concept updates remain valid in both modes
- applied subskill impact is stronger in `Practice` than in `Study`

### 6. Current emitted-event boundary

Given:
- runtime history produced only by the currently emitted event families

Then:
- the projector does not invent unsupported event-derived signals
- `recent_fatigue_signal` and `recent_abandonment_signal` stay at their explicit
  zero baseline
- concept and subskill updates still derive from reviewed evidence correctly

### 7. Review-due risk

Given:
- fragile or support-dependent success versus recent independent success

Then:
- `review_due_risk` is higher for fragile/support-dependent evidence
- recent independent successful evidence lowers `review_due_risk`

### 8. Mock-readiness conservatism

Given:
- only concept-recall reviewed evidence with no mock/follow-up signals

Then:
- `mock_readiness_estimate` may move only conservatively
- `mock_readiness_confidence` remains low relative to strong concept confidence

### 9. Idempotent rebuild

Given:
- the same runtime history replayed twice

Then:
- the projected learner profile is structurally and numerically equivalent
- no duplicate application or replay drift occurs

### 10. Output contract shape

Given:
- a projected profile with observed concept evidence and partial subskill support

Then:
- output keys follow canonical `content_id` / subskill identifiers
- unsupported subskills are absent rather than zero-filled
- `current_stage` is omitted unless source-of-truth semantics are defined before
  implementation
- timestamps are emitted in ISO-8601 UTC form

### 11. Unsupported subskills stay unknown

Given:
- current concept-recall evaluator outputs only the currently supported signals

Then:
- unsupported v1 subskills are absent/unknown, not synthesized as low values

## Test phases

### Phase 1: Pure projector rule tests

Add focused unit tests for:
- empty profile handling
- repeated evidence confidence growth
- support-damped evidence
- current emitted-event boundary behavior
- review-due risk behavior
- mock-readiness conservatism
- output contract shape
- deterministic rebuild

### Phase 2: Integration tests over real runtime/evaluation history

Use real `SessionRuntime` flows to assert:
- the projector consumes current session snapshots/events/evaluation results
- reviewed sessions produce concept updates
- support-use events alter projected dependency and confidence as expected
- projector output uses canonical keys and stable timestamp fields
- profile output remains stable under repeated rebuild

### Phase 3: Internal consumption seam only

If needed in the same slice:
- add a narrow internal service seam that recommendation can call later

Out of scope for this slice:
- public learner profile HTTP endpoints
- dashboard APIs

## Acceptance criteria

- repository contains a dedicated `learner_projection` module family
- projector builds a deterministic learner profile from current runtime history
- concept state, supported subskill state, and trajectory state are present
- sparse evidence stays distinct from confirmed weakness
- support-dependent success is represented as weaker evidence, not hard failure
- projector logic is covered by unit and runtime-integration tests
- no recommendation or frontend behavior changes are required to complete the
  slice

## Weak spots review

- current evaluator does not yet support all recommended v1 subskills, so
  `009` must explicitly tolerate partial subskill coverage
- current runtime history is process-local; learner profiles in this slice are
  therefore process-local as well
- current runtime does not yet emit `session_abandoned`, `session_completed`,
  `hint_requested`, `answer_revealed`, or `follow_up_*`, so large parts of the
  full learner-state rules remain intentionally dormant in `009`
- event payloads alone are not rich enough for the full projection; the
  projector will need to read stored evaluation results/session snapshots in
  addition to semantic event types
- `mock_readiness_*` will initially be conservative because existing evidence is
  not yet mock-heavy

## Hidden assumptions called out

- current reviewed units are concept-targeted enough for a first concept-state
  projection keyed by runtime/content metadata
- projection-time access to stored `last_evaluation_result` is acceptable in v1
  and does not violate the event model, because the event log remains the fact
  boundary while richer evaluation artifacts remain auditably stored
- the first projector output may be intentionally partial relative to the
  learner-profile example because `current_stage` semantics are not yet defined
- recommendation can remain on its current bootstrap context until `010`
  consumes the projector

## Recommended file/module posture

- `backend/src/sysdrill_backend/learner_projection.py`
- `backend/tests/test_learner_projection.py`

Optional helper split only if needed:
- small pure rule helpers under the same module family

## Source-of-truth review

- `docs/00_change_protocol.md`: respected; implementation slice only
- `docs/03_architecture/learner_state_update_rules_v1.md`: binding for update
  rules
- `docs/03_architecture/interaction_event_model.md`: binding for semantic event
  inputs
- `docs/03_architecture/implementation_mapping_v1.md`: binding for module
  ownership
- `docs/03_architecture/recommendation_policy_v1.md`: preserved; this slice only
  prepares its future input context
- `examples/schemas/learner-profile.example.yaml`: treated as structural shape
  guidance, with `current_stage` explicitly deferred pending source-of-truth
  semantics

## Change protocol expectations

- source-of-truth docs should remain unchanged unless implementation friction
  reveals a real contradiction
- ADR not expected unless the slice ends up needing a different persistence or
  ownership model
- v2.2 baseline should remain preserved
