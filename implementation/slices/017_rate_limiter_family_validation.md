# Slice 017: Rate Limiter Family Validation

## Status

- completed

## Execution posture

`017` is the first breadth-validation slice after completed `013`, `014`,
`015a`, `015b`, `015c`, and `016`.

Purpose:
- verify that the bounded mock-readiness path is not overfit to
  `URL Shortener`
- validate that evaluator-owned concept signals, projection updates, and
  recommendation follow-up remain correct for a second scenario family
- exercise authoring and materialization seams on one additional realistic
  family without reopening architecture

This slice is a portability check, not a semantic redesign.
It should confirm that the current contracts generalize to one more family
before expanding depth or breadth further.

## Goal

Add one bounded `Rate Limiter` scenario family that can pass through the
existing `MockInterview / ReadinessCheck` flow and produce correct
concept-specific negative-first remediation behavior.

Expected outcome:
- a `Rate Limiter` topic fixture exists with a minimal canonical concept pack
  and one bounded `mini_scenario`
- materialization produces a valid `scenario_readiness_check` unit for that
  family
- evaluator emits concept-specific negative signals for the actually weak
  `Rate Limiter` concept instead of a family-wide fallback
- learner projection updates only explicitly signaled `Rate Limiter` concepts
- recommendation selects truthful post-mock remediation for the weakened
  concept using existing `Practice / Remediate` and `Study / Reinforce`
  envelopes

## Why this slice exists

After `016`:
- concept-specific mock feedback is semantically honest again
- the binding docs define deterministic family-owned interpretation rules
- the runtime/evaluation/projection/recommendation loop works end to end for
  `URL Shortener`

What is still unproven:
- whether those same seams work for a second scenario family without special
  casing
- whether the current materialization and authoring contracts are portable
  beyond one hand-tuned family
- whether recommendation targeting remains concept-specific when the family has
  different gating conditions and evidence cues

`017` exists to validate architecture portability before adding:
- positive concept reinforcement
- more scenario families
- broader content production

## Affected bounded contexts

- `content_kernel`
- `learning_design`
- `evaluation_engine`
- `session_runtime`
- `learner_projection`
- `recommendation_engine`
- importer / authoring tooling

## Non-goals

- no new top-level mode
- no new runtime state or additional follow-up rounds
- no frontend redesign
- no positive-first or dual-polarity concept reinforcement
- no generic scenario-family framework rewrite
- no broad content seeding sweep
- no persistence redesign

## Constraints

- preserve the v2.2 implementation baseline
- preserve bounded-context ownership from
  `docs/03_architecture/implementation_mapping_v1.md`
- keep evaluator-owned concept interpretation
- keep `bound_concept_ids` as the allowed-concept set, not evidence by itself
- keep the first pass negative-first
- avoid family-specific hacks in `learner_projection` or `recommendation`
- keep the existing `MockInterview / ReadinessCheck` runtime contract intact

## Hidden assumptions to lock before code

- `Rate Limiter` is the only new family in scope
- one bounded `mini_scenario` is enough to validate portability for this slice
- existing UI/runtime surfaces should remain family-agnostic and require at
  most test updates, not behavior changes
- the current recommendation surface can address a `Rate Limiter` concept using
  existing structured actions without a new action type
- family validation is meaningful only if the family has canonical concepts,
  scenario binding, and fail-closed authoring validation together

## Architectural approaches considered

### Option A: Hand-authored fixture only

Shape:
- add one `Rate Limiter` fixture directly under test export content
- extend bindings/evaluator/runtime/projection/recommendation only as needed
- validate through backend tests

Pros:
- smallest implementation scope
- fastest way to validate portability of the main loop
- avoids importer churn if raw content is not ready

Cons:
- does not validate authoring/import pipeline portability
- risks another family working only because the fixture is hand-tuned
- gives weaker signal on content-production readiness

### Option B: Fixture plus bounded authoring-pipeline validation

Shape:
- add one `Rate Limiter` exported fixture
- ensure importer/validator understand the same content contract
- add at least one bounded tooling validation for the new family metadata

Pros:
- better matches watch areas from `00_implementation_baseline_v2.2.md`
- validates both runtime behavior and authoring portability
- reduces risk that the second family works only in test fixtures

Cons:
- slightly larger scope
- may surface importer friction that is orthogonal to the runtime path

## Recommendation

Choose Option B, but keep it narrow.

Reasoning:
- after `015a`, authoring validity is a load-bearing part of the scenario path
- breadth validation should test not only evaluator/projection portability, but
  also whether the content contract is usable for another family
- one bounded importer/validator pass is enough; this slice should not become a
  content-ingestion project

## Frozen decisions before code

### Family in scope

Only `Rate Limiter` is in scope for `017`.

Reasoning:
- `scenario_rubric_binding_v1.md` already defines `binding.rate_limiter.v1`
- it is structurally different enough from `URL Shortener` to validate
  portability
- it avoids reopening family prioritization

### Feedback posture

`017` stays negative-first.

Meaning:
- evaluator must emit explicit negative `concept_mock_evidence` for
  concept-specific weaknesses
- positive concept reinforcement remains out of scope for this slice
- acceptance should depend on truthful weakness targeting, not on strong mock
  success semantics

### Authoring contract

The `Rate Limiter` topic must include:
- minimal canonical concepts
- one bounded `mini_scenario`
- `bound_concept_ids` matching actual concept ids
- a `MockInterview / ReadinessCheck` materialization path without new schema
  fields

This slice should not introduce new content-schema surface area unless the
existing contract proves insufficient during TDD.

### Recommendation contract

After a reviewed weak `Rate Limiter` mock:
- primary follow-up should be `Practice / Remediate` for the actually weakened
  concept when the existing policy envelope allows it
- fallback may be `Study / Reinforce` when the weakness is low-confidence or
  when a lower-pressure follow-up is preferable
- no immediate `MockInterview` retry should be introduced by this slice

## Proposed concept pack

The first `Rate Limiter` concept pack should stay minimal and canonical:

- `concept.rate-limiter.algorithm-choice`
- `concept.rate-limiter.state-placement`
- `concept.rate-limiter.failure-handling`
- `concept.rate-limiter.trade-offs`

These concept ids should be sufficient to express:
- token bucket / leaky bucket / fixed-window semantics
- centralized vs distributed counter placement
- degraded behavior when state is unavailable or lagging
- correctness / latency / consistency trade-offs

## Binding expectations

`docs/03_architecture/scenario_rubric_binding_v1.md` already defines:
- required criteria
- secondary criteria
- gating conditions
- expected evidence cues

`017` should extend that family binding with concept-signal rules similar in
shape to `URL Shortener`, including:
- allowed concept ids
- anti-smear rule
- deterministic criterion/cue-to-concept mapping

Expected mapping direction:
- algorithm choice / rate-limiting semantics
  -> `concept.rate-limiter.algorithm-choice`
- centralized vs distributed counters / state placement
  -> `concept.rate-limiter.state-placement`
- unavailable or lagging state store handling
  -> `concept.rate-limiter.failure-handling`
- correctness vs latency trade-offs
  -> `concept.rate-limiter.trade-offs`

## TDD contract

Tests should be written before implementation.

### Content and tooling tests

`backend/tests/test_content_api.py`
- catalog/detail surfaces expose the new `Rate Limiter` topic and scenario
  metadata without regressing `URL Shortener`

`backend/tests/test_executable_learning_unit_materializer.py`
- `MockInterview / ReadinessCheck` materializes a `Rate Limiter`
  `scenario_readiness_check`
- invalid or dangling `bound_concept_ids` fail closed
- concept-recall paths remain unaffected

`tools/system-design-space-importer/tests/test_validator.py`
- `Rate Limiter` scenario metadata validates with matching `bound_concept_ids`
- dangling bound concepts or malformed family metadata are rejected

### Evaluator tests

`backend/tests/test_rule_first_evaluator.py`
- weak algorithm discussion emits a negative signal only for
  `concept.rate-limiter.algorithm-choice`
- weak state-placement discussion emits a negative signal only for
  `concept.rate-limiter.state-placement`
- failure-handling omission emits a negative signal only for
  `concept.rate-limiter.failure-handling`
- generic low weighted score without explicit criterion/cue gap does not emit a
  concept-specific signal
- emitted signals respect `bound_concept_ids`

### Runtime tests

`backend/tests/test_session_runtime.py`
- `Rate Limiter` mock follow-up evaluation requests include the correct
  `scenario_family`, `evaluation_binding_id`, and `bound_concept_ids`
- existing runtime state and follow-up limits remain unchanged

### Projection tests

`backend/tests/test_learner_projection.py`
- only explicitly signaled `Rate Limiter` concepts update
- unsignaled bound concepts do not move
- confidence-weighted scalar updates behave consistently with the `016`
  contract
- no raw scenario id leaks into concept state

### Recommendation tests

`backend/tests/test_recommendation_engine.py`
- recent weak `Rate Limiter` mock targets the actually weakened concept
- low-confidence weakness may fall back to `Study / Reinforce`
- recommendation does not select another immediate mock because of this slice
- `URL Shortener` behavior remains stable

### Summary tests

`backend/tests/test_learner_summary.py`
- weak `Rate Limiter` concept may surface in weak areas
- it does not become `review_due` unless existing fragility/recency rules
  justify it

## Acceptance criteria

- one bounded `Rate Limiter` family works through the existing
  `MockInterview / ReadinessCheck` loop
- evaluator emits concept-specific negative signals for the correct concept
- learner projection updates only explicitly signaled `Rate Limiter` concepts
- recommendation selects truthful post-mock remediation for the weakened
  concept
- importer/validator and runtime agree on the family content contract
- no new runtime state, action type, or UI flow is introduced
- `URL Shortener` regressions are covered by tests

## Weak spots to review before code

- if `Rate Limiter` concept boundaries prove too fuzzy, concept ids may need a
  narrower first-pass definition before implementation
- if importer validation requires broader raw-html extraction work, that part
  should be cut back to bounded validator coverage rather than expanding scope
- if recommendation targeting becomes ambiguous between
  `algorithm-choice` and `trade-offs`, the slice should prefer explicit
  criterion-driven targeting over score-based heuristics
- if current evaluator logic cannot produce deterministic negative signals for
  this family, stop and revise the binding doc before coding

## Source-of-truth review before code

Review and update as needed before implementation:
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`

Expected source-of-truth delta:
- likely update `scenario_rubric_binding_v1.md` for `Rate Limiter`
  `concept_signal_rules`
- docs should not require a new top-level contract unless TDD reveals a real
  gap

## Change protocol notes

Expected affected bounded contexts:
- `content_kernel`
- `learning_design`
- `evaluation_engine`
- `session_runtime`
- `learner_projection`
- `recommendation_engine`
- importer / authoring tooling

Expected source-of-truth files updated:
- likely `scenario_rubric_binding_v1.md`
- only update `evaluation_engine_v1.md`,
  `learner_state_update_rules_v1.md`, `content_schema.md`, or
  `authoring_model_v1.md` if TDD reveals a genuine contract gap

ADR required:
- likely no
- only if `017` uncovers a load-bearing mismatch that requires a new reusable
  family-binding abstraction

Schema/example files updated:
- at least one new topic fixture under
  `backend/tests/fixtures/export_root/system-design-space/`

Invariants intentionally preserved:
- bounded contexts remain separate
- recommendation selects structured learning actions
- top-level modes remain `Study`, `Practice`, `MockInterview`
- learner state remains `proficiency_estimate + confidence`
- v1 remains text-first

Baseline:
- this slice should preserve the v2.2 implementation baseline
