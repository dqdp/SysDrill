# Recommendation Policy v1

## Purpose

`Recommendation Policy v1` chooses the next **structured learning action** from a bounded action space using deterministic, explainable rules.

The policy is responsible for:
- candidate generation
- ranking
- guardrails
- session sizing
- rationale production

The policy is **not** responsible for turn-by-turn orchestration inside a session.

## Inputs

The policy consumes a normalized `RecommendationContext` containing:
- concept state summaries
- subskill state summaries
- trajectory state
- recent recommendation history
- review-due items
- available action templates
- policy constraints

## Action space

The policy selects among bounded `StructuredLearningAction` objects.

Each action contains:
- `mode`
- `session_intent`
- `target_type`
- `target_id`
- `difficulty_profile`
- `strictness_profile`
- `session_size`
- optional `delivery_profile`
- `rationale`

## Policy maturity phases

### 1. Bootstrap exploration
Used when learner evidence is still sparse.

Biases:
- broader signal collection
- lower strictness
- short sessions
- no aggressive remediation or mock escalation

### 2. Guided personalization
Used when evidence is emerging but not yet broadly sufficient.

Biases:
- targeted probes
- bounded remediation
- limited escalation
- mixed exploration and exploitation

### 3. Confident adaptation
Used when evidence is sufficiently strong across relevant areas.

Biases:
- more precise remediation
- stronger progression logic
- mock readiness checks where justified
- maintenance review without over-exploration

## Evidence sufficiency

The policy distinguishes:
- `insufficient`
- `emerging`
- `sufficient`

This distinction must be applied:
- globally for learner maturity
- locally for specific concepts, subskills, and readiness signals

Insufficient evidence must not be treated as confirmed weakness.

## Candidate generation

Candidate generation precedes ranking.

### Mode eligibility
- `Study` is broadly eligible
- `Practice` requires sufficient familiarity or controlled remediation framing
- `MockInterview` requires readiness thresholds and no blocking trajectory signals

### Intent eligibility
- `LearnNew` when evidence is sparse
- `Reinforce` when performance is promising but still unstable
- `Remediate` when weakness is repeated and sufficiently evidenced
- `SpacedReview` when review due risk is high
- `ReadinessCheck` when readiness estimate and confidence justify it

### Target selection
- `Study` usually targets concepts or concept clusters
- `Practice` usually targets concepts through applied units or subskills through bounded drills
- `MockInterview` usually targets scenario families or explicit scenarios

## Ranking

Ranking is heuristic and deterministic in v1.

The policy must distinguish between:
- a **policy envelope** that protects completion likelihood and momentum
- the **content-facing priority order** among admissible actions

### Policy envelope

Completion likelihood and momentum act as a top-level moderating envelope, not as the primary instructional objective.

This means the policy should avoid recommending actions that are likely to fail due to:
- high recent fatigue
- elevated recent abandonment signal
- excessive strictness for the current trajectory
- excessive session size for the current trajectory

The policy may therefore downrank or suppress otherwise useful actions when completion risk is too high.

### Priority order among admissible actions

Once completion and fatigue guardrails are satisfied, ranking in v1 follows this general priority order:

1. **Remediation of confirmed weaknesses**
2. **Spaced review due maintenance**
3. **Progression / readiness escalation**

This order applies only when weakness is sufficiently evidenced. Insufficient evidence must not be treated as confirmed weakness.

### Priority interpretation

#### 1. Remediation of confirmed weaknesses
Remediation receives the highest instructional priority when:
- weakness is repeated
- weakness has sufficient confidence
- the learner is not already trapped in an over-remediation loop

#### 2. Spaced review due maintenance
Spaced review outranks progression when maintenance is overdue, but it does not permanently override all other needs.

#### 3. Progression / readiness escalation
Progression and readiness escalation are valuable, but they come after confirmed remediation needs and overdue maintenance.

### Ranking signals

Primary ranking signals:
- weakness severity
- confidence-adjusted readiness
- review due risk
- completion likelihood
- novelty/diversity
- freshness of previous recommendations
- momentum preservation

### Ranking bias rule

The v1 policy is:
- slightly biased toward completion and momentum when weakness is not high-confidence critical
- strongly biased toward remediation when weakness is repeated and high-confidence

## Guardrails

Guardrails override ranking when necessary.

### Required guardrails
- no endless remediation loops
- no premature mock escalation
- no repeated identical action patterns
- protect completion under fatigue
- preserve maintenance review
- no illegal action combinations

## Session sizing

Session size is part of the recommendation decision.

Profiles:
- `short`
- `standard`
- `extended`

v1 should prefer `short` and `standard` by default.

## Rationale

Every recommendation must include a rationale that explains:
- why this action
- why now
- why not a nearby alternative

## Non-goals

The v1 policy does not:
- generate arbitrary curricula
- orchestrate intra-session runtime behavior
- rely on opaque learned ranking
- optimize only for maximal challenge

## Core normative statements

1. Recommendation ranks structured learning actions, not raw content items.
2. Candidate generation precedes ranking.
3. Insufficient evidence must remain distinct from confirmed weakness.
4. Escalation requires both estimate and confidence.
5. Remediation must be bounded.
6. Session size is part of the recommendation decision.
7. Guardrails override ranking where needed.
8. Every decision must be rationale-bearing and versioned.
9. Completion likelihood and momentum constrain policy aggressiveness before instructional ranking is applied.
10. Among admissible actions, confirmed remediation outranks spaced review due maintenance, which outranks progression/readiness escalation.
