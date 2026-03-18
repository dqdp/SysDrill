# Slice 004: Executable Learning Unit Materialization

## Status

- completed

## Goal

Materialize deterministic `ExecutableLearningUnit` shapes from loaded topic
bundles plus bundled learning-design hints without collapsing `Content Kernel`,
`Learning Design`, and `Session Runtime`.

## Why this is on the critical path

The backend can now load topic bundles and expose a read-only catalog, but later
runtime slices must not orchestrate directly from raw topic-package payloads.

This slice creates the first bounded hand-off from loaded canonical content to
runtime-ready learning units.

## In scope

- a backend materializer module for `ExecutableLearningUnit`
- deterministic derivation for one narrow unit family: concept recall
- use of bundled `learning_design_drafts.candidate_card_types` as advisory
  learning-design input
- mode/intent-compatible unit materialization for supported combinations
- stable unit ids and stable source-content references
- targeted unit tests for deterministic ordering and contract shape

## Out of scope

- session creation or runtime state transitions
- recommendation ranking or action generation
- evaluation execution
- `MockInterview` unit materialization
- scenario-family and mini-scenario unit derivation
- comparison / failure / sequencing / oral variants
- API endpoint expansion for executable units

## Affected bounded contexts

- `Content Kernel`
- `Learning Design`
- implementation-side backend infrastructure around learning-unit derivation

## Source-of-truth references

- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/02_domain/learning_design_boundary.md`
- `docs/02_domain/hand_off_contracts.md`
- `docs/02_domain/domain_model.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- `implementation/slices/003_content_catalog_api_surface.md`
- `implementation/slices/003a_content_catalog_hardening.md`

## Architectural options considered

### Option A: Narrow concept-recall materializer

- derive only `concept_recall` units
- use explicit supported `(mode, session_intent)` combinations
- use a small deterministic policy table for hint/follow-up/completion metadata
- keep output as a backend-internal seam for later runtime slices

Trade-offs:
- smallest correct step
- matches current topic-package coverage and authoring hints
- leaves scenario/mock and richer learning-design coverage for later slices

### Option B: Generic multi-family learning-design compiler

- derive concept, pattern, and scenario units
- support multiple card families from the start
- pre-bake broader mode/intent coverage and evaluation bindings

Trade-offs:
- better long-term coverage
- materially higher design ambiguity right now
- risks inventing learning-design and evaluation contracts not yet fixed in docs

Decision:
- choose Option A for this slice

## Proposed implementation shape

- add `backend/src/sysdrill_backend/executable_learning_unit_materializer.py`
- add `backend/tests/test_executable_learning_unit_materializer.py`
- keep the first surface as a pure Python materialization helper, not an API
- accept loaded bundle/catalog inputs explicitly; do not read exporter files
  directly from this module

## Supported derivation posture

For the first implementation wave, this slice should materialize only
`concept_recall` units when:
- the topic bundle advertises `learning_design_drafts.candidate_card_types`
  including `recall`
- the topic contains at least one concept
- the requested mode/intent combination is explicitly supported by the local
  materialization policy

Recommended supported combinations for this slice:
- `Study + LearnNew`
- `Study + Reinforce`
- `Study + SpacedReview`
- `Practice + Reinforce`
- `Practice + Remediate`

Explicitly unsupported for this slice:
- any `MockInterview` combination
- `ReadinessCheck`
- scenario-driven unit families

## Local implementation contract

Because some `ExecutableLearningUnit` sub-fields are named in docs but not fully
schema-specified, this slice should define a narrow internal contract:

- `allowed_hint_levels`: list of integer hint levels available to the unit
- `follow_up_envelope`: mapping with deterministic max-follow-up metadata
- `completion_rules`: mapping with deterministic answer-boundary metadata

This contract is implementation-local for v1 slice work and should not be
treated as a public API.

## Evaluation-binding posture

The docs require `evaluation_binding_id`, but current binding docs are scenario-
centric and do not yet define concept-recall/card bindings.

For this slice:
- materialized concept-recall units should carry a deterministic internal
  binding id
- the binding id should remain stable and explicit
- this does not revise the scenario binding docs and does not imply evaluation
  execution is ready for recall units yet

## Test contract

- materializer returns deterministically ordered `concept_recall` units from a
  loaded valid catalog
- unit ids are stable across repeated materialization
- `source_content_ids` preserve stable content ids from canonical content
- materializer only emits units for topics advertising `recall`
- materializer skips topics with no concepts
- supported `Study` and `Practice` mode/intent combinations materialize units
- unsupported mode/intent combinations fail closed with explicit errors
- `MockInterview` is rejected for this unit family
- `visible_prompt` is derived deterministically from canonical concept data
- `pedagogical_goal` is explicit and stable
- `allowed_hint_levels`, `follow_up_envelope`, and `completion_rules` are
  deterministic and mode-aware
- `evaluation_binding_id` is explicit and stable for the unit family
- materialization does not mutate the loaded catalog

## Acceptance criteria

- runtime-facing code can consume `ExecutableLearningUnit` shapes instead of raw
  topic bundles
- the implementation preserves the `Content Kernel -> Learning Design ->
  Runtime` seam
- the first unit family is deterministic, auditable, and narrow
- the slice creates no implicit recommendation or runtime orchestration logic
- the chosen design can be extended later to richer unit families without
  rewriting the current contract

## Weak spots and assumption review

- hidden assumption: bundled `learning_design_drafts` are sparse advisory inputs,
  not a complete learning-design schema; this slice intentionally uses them only
  as eligibility hints
- hidden assumption: concept recall is the safest first unit family because
  current exporter output already advertises `recall`, while scenario/mock
  derivation would require more binding decisions
- weak spot: docs require `evaluation_binding_id`, but recall/card binding docs
  do not yet exist; this slice should use a narrow internal binding id and avoid
  pretending evaluation readiness beyond that
- weak spot: docs name `allowed_hint_levels`, `follow_up_envelope`, and
  `completion_rules`, but do not fully specify nested schema; this slice must
  keep their shapes small and local
- mismatch noted: evaluation docs reference `unit_family`, while
  `ExecutableLearningUnit` fields in the domain model do not; this slice should
  not widen the unit contract to solve that prematurely
- no contradiction found with the v2.2 baseline, bounded-context ownership, or
  ADR-level frozen decisions
- no ADR is required if the implementation remains within this narrow
  materialization posture

## Verification

- targeted unit tests for deterministic materialization behavior
- `make verify-python`

## Definition of done

- explicit TDD tests exist for supported and unsupported derivation cases
- a backend materializer module exists for deterministic `concept_recall` units
- generated unit shapes satisfy the agreed internal contract
- roadmap/status remain synced
- the v2.2 implementation baseline remains preserved

## Outcome

- backend now materializes deterministic `concept_recall` `ExecutableLearningUnit`
  shapes from loaded topic bundles
- materialization stays bounded to explicit supported `Study` and `Practice`
  mode/intent combinations
- unsupported combinations fail closed with explicit domain errors
- implementation remains backend-internal and does not yet widen the API surface
