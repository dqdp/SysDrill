# Metrics and Assurance

## Why assurance matters
The system teaches and evaluates. It must therefore be engaging, explainable, and auditable.

This document defines:
- product and system metrics to observe in production;
- core audit questions;
- telemetry boundaries for v1.

It does **not** define the detailed evaluation-subsystem QA procedure.
That lives in `evaluation_quality_plan_v1.md`.

## Product metrics
- weekly active learners
- sessions per learner per week
- scenario completion rate
- mock interview completion rate
- review revisit rate
- recommendation acceptance rate
- recommendation completion rate by action type

## Learning metrics
- recall success rate
- hint usage trend
- rubric score trend
- weak-area remediation rate
- review queue completion rate
- spaced-review compliance rate
- articulation-readiness trend

## Recommendation and trajectory metrics
- recommendation skip rate by action type
- recommendation completion rate by mode/intent
- repeated remediation loop incidence
- progression-to-mock conversion rate
- abandonment rate after recommendation acceptance
- short-session versus standard-session completion trend

## System and contract health metrics
- semantic event append success rate
- learner projection lag
- recommendation decision generation latency
- evaluation completion latency
- degraded-evaluation mode incidence
- version-mismatch or binding-mismatch incidence

## Quality and trust metrics
- perceived fairness of scoring
- usefulness of feedback
- alignment of perceived and measured difficulty
- hallucination incident rate in tutor explanations
- recommendation dissatisfaction rate

## Assurance artifacts that must be stored
- evaluation outputs with rubric and binding provenance
- recommendation decisions with rationale and action-contract fields
- semantic event trail for major session steps
- content version used in each session
- mode and session intent used in each session
- evaluator/model version used for assisted evaluation
- policy version and decision mode for recommendation

## Minimal audit questions
1. Why was this structured learning action recommended?
2. Which interaction events updated learner state?
3. Which content, rubric, and binding versions were used?
4. Which part of scoring was rule-based and which part was model-assisted?
5. Did remediation loop without progress?
6. Did low-level UI exhaust leak into learner evidence?
7. Was a weak recommendation made under insufficient evidence?
8. Did fatigue/abandonment signals cap session aggressiveness as intended?

## Package links
- runtime flow contract: `docs/03_architecture/session_runtime_state_machine_v1.md`
- evaluation engine contract: `docs/03_architecture/evaluation_engine_v1.md`
- evaluation QA plan: `docs/05_ops/evaluation_quality_plan_v1.md`
- recommendation decision trace: `docs/05_ops/recommendation_decision_logging_and_offline_evaluation.md`

## Telemetry boundary for v1
Only semantic learning events with coarse timing summaries count as learner evidence. Raw UI exhaust, per-edit traces, and interim voice telemetry may exist separately as infra/product analytics, but not as first-class learner-evidence events without a new decision.
