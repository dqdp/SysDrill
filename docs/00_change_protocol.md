# Change Protocol

Use this protocol when modifying the knowledge base or implementing code against it.

## Baseline rule
v2.2 is the current implementation baseline. Preserve it by default. Use implementation friction, tests, and observed mismatches to justify revisions.

## When an ADR is required
Create or update an ADR if a change affects:
- bounded context ownership
- modes model or session intent semantics
- recommendation scope or policy surface
- learner evidence semantics
- evaluation model or rubric posture
- authoring posture
- text-first vs voice-first posture
- any frozen baseline decision listed in `docs/00_implementation_baseline_v2.2.md`

## When a local doc update is enough
A local update is enough for:
- clarifications that do not change behavior
- examples and schema alignment
- non-load-bearing wording improvements
- implementation details that preserve existing contracts
- tightening a watch area without changing a frozen decision

## Required sync sets
### Domain entity changes
Update:
- `docs/02_domain/domain_model.md`
- related contract docs
- affected schema examples

### Runtime flow changes
Update:
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`

### Learner state or recommendation changes
Update:
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/recommendation_engine_surface.md`
- relevant schema examples

### Evaluation changes
Update:
- `docs/04_content/rubric_schema.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/05_ops/evaluation_quality_plan_v1.md`

### Baseline status changes
Update:
- `AGENTS.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/00_source_of_truth_map.md`
- `docs/00_release_notes.md`

## Before finishing a change set
- verify source-of-truth files remain aligned
- update examples if payloads changed
- update release notes for meaningful package changes
- state whether an ADR was required
- state whether the v2.2 implementation baseline was preserved or intentionally revised
