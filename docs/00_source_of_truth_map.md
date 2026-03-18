# Source of Truth Map

This file tells implementation agents which documents are authoritative for which questions.

## Baseline implementation status
- implementation baseline summary: `docs/00_implementation_baseline_v2.2.md`
- repository operating contract for agents: `AGENTS.md`
- package change history: `docs/00_release_notes.md`

## Product mission and scope
- `docs/01_product/product_mission_and_scope.md`
- `docs/01_product/personas_and_skill_model.md`

## FPF framing and package purpose
- `docs/00_fpf_application.md`
- `README.md`

## Bounded contexts and ownership
- `docs/02_domain/bounded_context_map.md`
- `docs/02_domain/learning_design_boundary.md`

## Domain entities and contracts
- `docs/02_domain/domain_model.md`
- `docs/02_domain/hand_off_contracts.md`

## Modes model and session intent
- `docs/adr/ADR-005_modes_model_and_session_intent.md`
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`

## Recommendation scope
- `docs/adr/ADR-006_structured_recommendation_action_scope.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/recommendation_engine_surface.md`

## Event granularity
- `docs/adr/ADR-007_semantic_event_granularity_v1.md`
- `docs/03_architecture/interaction_event_model.md`

## Authoring posture
- `docs/adr/ADR-008_bundled_authoring_and_progressive_coverage_v1.md`
- `docs/04_content/authoring_model_v1.md`
- `docs/04_content/content_schema.md`

## Learner state semantics
- `docs/adr/ADR-009_evidence_weighted_proficiency_and_confidence_state.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `examples/schemas/learner-profile.example.yaml`

## Deterministic policy surface and later model extension
- `docs/adr/ADR-010_deterministic_policy_surface_with_future_model_extension.md`
- `docs/03_architecture/recommendation_engine_surface.md`
- `docs/05_ops/recommendation_decision_logging_and_offline_evaluation.md`

## Evaluation rules
- `docs/04_content/rubric_schema.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/03_architecture/concept_recall_binding_v1.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/05_ops/evaluation_quality_plan_v1.md`

## Runtime flow and event emission
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`

## Implementation mapping
- module/code-boundary mapping: `docs/03_architecture/implementation_mapping_v1.md`
- runtime topology and sync/async seams: `docs/03_architecture/target_architecture_v1.md`
- evaluation pipeline contract: `docs/03_architecture/evaluation_engine_v1.md`

## Operational metrics and release history
- `docs/05_ops/metrics_and_assurance.md`
- `docs/00_release_notes.md`
