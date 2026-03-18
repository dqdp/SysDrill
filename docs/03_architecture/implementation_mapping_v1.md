# Implementation Mapping v1

## Purpose
This document maps the documentation system to expected code/module boundaries for v1 implementation.

It exists to help implementation agents translate bounded contexts and contracts into a repository/module layout without collapsing architectural seams.

## Mapping principle
v1 may be deployed as a monolith, but the code should preserve domain seams as if they were potential future service seams.

## Expected module families

## 1. content_kernel
Maps from:
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`

Should own:
- content loading/materialization
- concept/pattern/scenario repositories
- version references
- scenario binding lookup
- rubric lookup

## 2. learning_design
Maps from:
- `docs/02_domain/learning_design_boundary.md`
- `docs/04_content/authoring_model_v1.md`

Should own:
- card/exercise template resolution
- transformation from canonical content to executable learning units
- delivery-profile metadata
- mode/intent-compatible unit selection helpers

## 3. session_runtime
Maps from:
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`

Should own:
- session creation from recommendation action
- runtime state machine
- event emission at semantic boundaries
- hint/reveal handling
- answer boundary capture
- handoff to evaluation

## 4. evaluation_engine
Maps from:
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/04_content/rubric_schema.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`

Should own:
- evaluation context assembly
- rule-based evidence extraction
- model-assisted interpretation hooks
- criterion assembly
- score aggregation
- review artifact generation

## 5. learner_projection
Maps from:
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/interaction_event_model.md`

Should own:
- concept/subskill/trajectory projections
- review-due projection
- mock-readiness projection
- idempotent event/evaluation consumption

## 6. recommendation_engine
Maps from:
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/recommendation_engine_surface.md`
- `docs/05_ops/recommendation_decision_logging_and_offline_evaluation.md`

Should own:
- recommendation context assembly
- candidate generation
- ranking
- guardrail enforcement
- rationale generation
- decision persistence/logging

## 7. web_api / ui
Maps from:
- `docs/views/product_view.md`
- `docs/views/engineering_view.md`

Should own:
- session APIs
- recommendation APIs
- learner dashboard APIs
- review surfaces
- weak-area/readiness surfaces

## Persistence ownership guidance
- runtime session records belong with `session_runtime`
- evaluation records belong with `evaluation_engine`
- semantic event log is shared infrastructure but schema-governed by runtime/evidence contracts
- learner state projections belong with `learner_projection`
- recommendation decisions belong with `recommendation_engine`
- content materialization belongs with `content_kernel`

## Cross-module contracts that must stay explicit
- runtime -> evaluation request
- runtime -> event log append
- evaluation -> learner downstream signals
- event/evaluation -> learner projector inputs
- learner state -> recommendation context
- recommendation decision -> runtime action acceptance

## Anti-collapse rules
- do not fold recommendation ranking into runtime orchestration
- do not let evaluation mutate learner state directly
- do not let content authoring objects become runtime blobs
- do not bypass event logging with direct learner-state mutation
- do not let UI-level analytics become learner evidence by default
