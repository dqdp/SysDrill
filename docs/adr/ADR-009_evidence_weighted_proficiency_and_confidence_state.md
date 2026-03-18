# ADR-009: Evidence-Weighted Proficiency and Confidence State

Status: Accepted

## Context

Earlier drafts used `mastery` as the main learner-state term. For v1 this is too strong and implies a level of certainty the platform does not actually have. The system observes bounded semantic learning events, rubric-based evaluations, support usage, and session outcomes. It does not directly observe true capability.

At the same time, recommendation policy needs more than a flat score. It must distinguish:
- confirmed weakness;
- confirmed strength;
- insufficient evidence;
- support-dependent performance;
- fragile vs recent performance.

## Decision

The learner model for v1 will use **evidence-weighted proficiency estimates plus confidence**, rather than `mastery` as a primary state primitive.

The minimum learner-state surface for v1 consists of:
- **concept state**: `proficiency_estimate`, `confidence`, `review_due_risk`, `hint_dependency_signal`, `last_evidence_at`;
- **subskill state**: `proficiency_estimate`, `confidence`, `last_evidence_at`;
- **trajectory state**: `recent_fatigue_signal`, `recent_abandonment_signal`, `mock_readiness_estimate`, `mock_readiness_confidence`, `last_active_at`.

The model intentionally avoids first-class state for:
- every card type;
- every scenario instance or scenario family;
- learner personality / preference profiling;
- low-level event-family-specific confidence buckets.

## Update stance

The update model remains heuristic and explainable in v1.

- `evaluation_attached` is the primary proficiency update event.
- `hint_requested` dampens positive evidence weight and increases support dependency, but does not equal failure.
- `answer_revealed` is a stronger support-needed signal than hint use.
- `follow_up_answered` updates articulation, defense, and trade-off subskills more strongly than raw concept proficiency.
- `session_abandoned` updates trajectory state more than knowledge state.
- mode weighting is required: `Mock Interview` > `Practice` > `Study` for applied-readiness signals.
- confidence grows from repeated, completed, moderately consistent evidence, not from a single strong attempt.

## Consequences

Positive:
- recommendation can distinguish weak from unknown;
- learner state becomes more honest and explainable;
- mock-readiness and remediation logic become less brittle;
- event model and evaluation model align with bounded evidence.

Trade-offs:
- the learner profile becomes slightly richer than a simple score map;
- downstream documents must avoid the misleading language of absolute mastery;
- thresholds and heuristics must be documented carefully.
