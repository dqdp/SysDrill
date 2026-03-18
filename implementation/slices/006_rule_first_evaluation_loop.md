# Slice 006: Rule-First Evaluation Loop

## Status

- completed

## Goal

Produce the first deterministic `EvaluationResult` and review output for the
manual runtime path using a rule-first evaluator over the current
`concept_recall` executable unit family.

## Why this is on the critical path

Milestone B already has:
- manual session start
- bounded unit presentation
- answer submission
- append-only semantic events
- explicit evaluation hand-off payload

The next missing step is deterministic review output.

Without this slice, the prototype stops at `evaluation_pending` and the learner
never receives an auditable review artifact.

## In scope

- a pure rule-first evaluator for `binding.concept_recall.v1`
- deterministic `EvaluationResult` assembly without LLM assistance
- deterministic review-summary generation for the bounded prototype path
- runtime support for attaching evaluation and exposing review output
- semantic event emission for `evaluation_attached` and `review_presented`
- targeted backend tests for evaluator logic, runtime transitions, and API wiring
- minimal contract hardening of runtime `evaluation_request` where current fields
  are insufficient for evaluation

## Out of scope

- scenario-family evaluation
- model-assisted interpretation
- learner-state projection
- recommendation updates
- persistence beyond in-memory prototype stores
- hint/reveal endpoint expansion
- frontend implementation
- broad rubric redesign

## Affected bounded contexts

- `Evaluation Engine`
- `Session Runtime`
- `web_api / ui`

## Source-of-truth references

- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/02_domain/hand_off_contracts.md`
- `docs/02_domain/domain_model.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/04_content/rubric_schema.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `implementation/roadmap.md`
- `implementation/status.md`
- `implementation/slices/005_session_runtime_and_event_log_bootstrap.md`

## Architectural options considered

### Option A: Narrow rule-first evaluator for `concept_recall`

- introduce a pure evaluator for the currently materialized unit family
- use a small deterministic criterion set aligned to concept explanation quality
- keep `evaluation_mode = rule_only`
- drive runtime from `evaluation_pending` to `review_presented`

Trade-offs:
- shortest path to a demoable review loop
- aligned with the current runtime and materialized units
- requires an explicit concept-recall binding contract because current binding
  docs are scenario-centric

### Option B: Generic scenario-family evaluator first

- implement evaluator strictly around scenario-family bindings from
  `scenario_rubric_binding_v1.md`
- defer concept-recall review until scenario units exist

Trade-offs:
- cleaner match to the current binding docs
- not aligned with the runtime that exists today
- slows Milestone B by forcing scenario-family unit work first

Decision:
- choose Option A for this slice

## Proposed implementation shape

- add `backend/src/sysdrill_backend/rule_first_evaluator.py`
- extend `backend/src/sysdrill_backend/session_runtime.py`
- extend `backend/src/sysdrill_backend/app.py` with minimal evaluation/review endpoints
  only if runtime attachment cannot stay behind existing endpoints
- add `backend/tests/test_rule_first_evaluator.py`
- extend `backend/tests/test_session_runtime.py`
- add `backend/tests/test_evaluation_api.py` only if endpoint coverage becomes
  too large for existing test files

## TDD plan

### Phase 1: evaluator contract tests first

Create evaluator-focused tests that fail before implementation.

Test contract:
- empty transcript yields low-confidence evaluation and cannot receive strong
  criterion coverage
- very short transcript yields degraded confidence
- transcript that only defines the concept covers explanation basics but leaves
  usage and trade-offs missing
- transcript that covers what the concept is, when to use it, and trade-offs
  scores materially higher than a definition-only answer
- the same transcript is judged more strictly in `Practice` than in `Study`
- support-dependent inputs such as hint usage or answer reveal reduce confidence
  and independence-oriented downstream signals
- evaluator keeps `observed_evidence` separate from `inferred_judgment`
- evaluator output is deterministic across repeated runs

### Phase 2: runtime transition tests

Extend runtime tests before implementation.

Test contract:
- session in `evaluation_pending` can attach an evaluation result
- attaching evaluation emits `evaluation_attached`
- generating review emits `review_presented`
- rejected evaluation attachment from the wrong state fails closed
- attaching evaluation does not rewrite prior events
- runtime snapshot exposes the latest evaluation and review artifacts for the
  current session

### Phase 3: API tests

Add API-level regression tests before implementation.

Test contract:
- review output is retrievable for a session that has a valid pending evaluation
- unknown `session_id` returns `404`
- evaluating a session from the wrong state returns an explicit `400` or `409`
- malformed evaluation requests do not surface incidental `500`
- response shape is deterministic and includes `evaluation_result` and
  `review_summary`

## Expected evaluation contract for this slice

### Evaluation input

This slice should use the runtime hand-off as the starting point, but harden it
to include at least:
- `session_id`
- `session_mode`
- `session_intent`
- `executable_unit_id`
- `unit_family`
- `binding_id`
- `transcript_text`
- `hint_usage_summary`
- `answer_reveal_flag`
- `timing_summary`
- `completion_status`
- `strictness_profile`

If the current runtime hand-off lacks `unit_family`, this slice should add it
before evaluator logic is introduced.

### Evaluation output

The first evaluator should return:
- `evaluation_id`
- `session_id`
- `unit_id`
- `criterion_results`
- `gating_failures`
- `weighted_score`
- `overall_confidence`
- `missing_dimensions`
- `review_summary`
- `downstream_signals`
- `binding_version_ref`
- `evaluation_mode = rule_only`
- `evaluator_version_ref`

## Local implementation posture

Because the current source-of-truth bindings are scenario-centric, this slice
should define a narrow internal concept-recall evaluation contract:

- criterion coverage is limited to the concept-recall task, not full scenario
  design quality
- no LLM interpretation is used
- hard gating should be minimal and explicit
- review output should remain short, deterministic, and auditable

This is a prototype-local contract and should not pretend to be the final
generic evaluator surface.

## Review output posture

For this slice, review output should include:
- strengths
- missing dimensions
- shallow areas
- next-focus suggestion
- support-dependence note when relevant

The output should be deterministic and derived from criterion results plus
support/confidence signals.

## Acceptance criteria

- backend can produce deterministic evaluation and review output for the manual
  `concept_recall` session path
- runtime advances beyond `evaluation_pending` with explicit semantic events
- evaluator is rule-first and auditable
- evidence and judgment remain separate
- no learner-state mutation or recommendation logic is introduced
- Milestone B moves from answer submission to deterministic reviewed outcome

## Verification

- targeted evaluator tests
- targeted runtime transition tests
- targeted API tests
- `PYTHONPATH=src python3.12 -m pytest -q tests`

## Definition of done

- explicit TDD tests exist for evaluator behavior, runtime transitions, and API
  error handling
- a pure rule-first evaluator module exists for `concept_recall`
- runtime emits `evaluation_attached` and `review_presented`
- review output is deterministic and explainable
- roadmap/status remain synced
- source-of-truth docs are updated if this slice hardens the runtime ->
  evaluation contract

## Weak spots and assumption review

- mismatch: `implementation/roadmap.md` currently says "one bounded scenario
  family", while the current runtime only materializes `concept_recall` units
- weak spot: current binding docs do not define `binding.concept_recall.v1`
- weak spot: current runtime `evaluation_request` is still narrower than the
  evaluation-engine input contract in `evaluation_engine_v1.md`
- assumption: a bounded concept-recall evaluator is acceptable as the first
  review loop if it is declared explicitly rather than disguised as a generic
  scenario evaluator
- no contradiction with bounded-context ownership is introduced if the slice
  stays narrow and keeps evaluation logic out of runtime orchestration

## Pre-code alignment note

Recommended alignment before implementation:

1. Treat Slice 006 as explicitly scoped to one bounded executable-unit family,
   `concept_recall`, rather than to a scenario family that does not yet exist
   in the runtime path.
2. Document `binding.concept_recall.v1` as a narrow prototype binding instead
   of leaving it as a code-only constant.
3. Harden the runtime -> evaluation hand-off to include `unit_family` before
   evaluator logic is written.
4. Stop the first implementation at `review_presented` unless a concrete UI
   requirement makes `completed` necessary in the same slice.

## ADR check

An ADR is not required if this slice:
- preserves rubric-first posture
- keeps evaluation separate from learner-state mutation
- treats the concept-recall binding as a narrow local extension rather than a
  redesign of evaluation architecture

If the roadmap wording or binding posture is treated as a load-bearing decision,
revisit ADR need before implementation.

## Expected doc sync set if implementation proceeds

If this slice changes runtime -> evaluation payload shape or formalizes the
concept-recall binding, update:
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/04_content/rubric_schema.md` only if criterion semantics change
- binding docs via either an extension to
  `docs/03_architecture/scenario_rubric_binding_v1.md` or a new companion
  binding doc for concept-recall
