# Implementation Baseline v2.2

v2.2 is the current **implementation baseline** for the first controlled implementation wave.

This file summarizes what is frozen, what is implementation-ready, and what should be treated as watch areas rather than blockers.

## Frozen baseline decisions
The following decisions should be treated as fixed unless explicitly revised by ADR:
- normalized knowledge base as source of truth
- recommendation as a separate bounded context
- text-first before voice
- rubric-first hybrid evaluation
- top-level modes: `Study`, `Practice`, `MockInterview`
- `Review` as artifact/intent layer, not a top-level mode
- recommendation as a structured learning action
- semantic event granularity with coarse timing only
- bundled authoring with schema-distinct content and progressive coverage in v1
- learner state as `proficiency_estimate + confidence`
- deterministic recommendation surface with future model-assisted extension
- maturity-aware exploration/exploitation stance
- deterministic guardrails remain deterministic even if scoring later becomes model-assisted

## Implementation-ready source of truth
These documents may be used directly as build-facing contracts:
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/recommendation_engine_surface.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/rubric_schema.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/04_content/authoring_model_v1.md`
- all ADRs in `docs/adr/`

## Orientation-only documents
These documents are useful for context and framing, but they should not override the contracts above in case of conflict:
- `README.md`
- `docs/00_document_map.md`
- `docs/01_product/*`
- `docs/views/*`
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/learner_model_and_recommendation_v1.md`
- `docs/05_ops/roadmap_v1_v2.md`

## Watch areas during implementation
The following are real implementation watch areas, but not blockers for starting:
- target architecture to code mapping and first deploy slices
- evaluation engine practical score/evidence behavior
- runtime and emitted-event alignment
- recommendation policy tuning against real completion and UX behavior
- authoring velocity under real bundle creation

## Working rule
Implementation should now be preferred over speculative redesign. Use real friction and test evidence to justify further hardening.
