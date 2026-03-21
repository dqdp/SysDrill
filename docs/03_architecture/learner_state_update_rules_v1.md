# Learner State Update Rules v1

## Purpose

This document defines how semantic learning events and evaluation outputs update the v1 learner model.
It is intentionally heuristic, interpretable, and bounded. It does not attempt to infer true mastery.

## State model stance

The v1 learner model maintains **proficiency estimates plus confidence**, not absolute mastery.
This lets the system distinguish:
- confirmed weakness;
- confirmed strength;
- insufficient evidence;
- support-dependent performance.

## Minimum state dimensions

### Concept state
For each concept:
- `proficiency_estimate`
- `confidence`
- `review_due_risk`
- `hint_dependency_signal`
- `last_evidence_at`

### Subskill state
For each subskill:
- `proficiency_estimate`
- `confidence`
- `last_evidence_at`

Recommended v1 subskills:
- `constraint_discovery`
- `decomposition`
- `tradeoff_reasoning`
- `failure_mode_awareness`
- `communication_clarity`
- `structured_articulation`
- `answer_defense_under_followup`

### Trajectory state
At learner level:
- `recent_fatigue_signal`
- `recent_abandonment_signal`
- `mock_readiness_estimate`
- `mock_readiness_confidence`
- `last_active_at`

## Evidence families

### 1. Performance evidence
Signals about answer quality and applied reasoning.
Sources:
- `evaluation_attached`
- `follow_up_answered`
- completed `answer_submitted` when evaluation later attaches

### 2. Independence evidence
Signals about how much support was needed.
Sources:
- `hint_requested`
- `answer_revealed`

### 3. Engagement evidence
Signals about completion, continuation, and session durability.
Sources:
- `session_completed`
- `session_abandoned`
- `recommendation_accepted`
- `recommendation_completed`

### 4. Recency evidence
Signals driven by time since last meaningful attempt.
Sources:
- timestamps on semantic events

Interpretation rule:
Recency-sensitive updates should compare evidence timestamps against the current
evaluation time, not only against the newest event already present in the
rebuilt learner profile.

## Primary update event

`evaluation_attached` is the primary proficiency update event in v1.
It should carry or reference:
- rubric subscores;
- target concepts;
- target subskills;
- downstream learner-model signals;
- evaluation confidence;
- missing dimensions and weaknesses;
- overall outcome band.

`answer_submitted` establishes an attempt boundary, but by itself should not strongly move proficiency.

## Mode weighting

The same observed quality should not update state equally across modes.

### Study
Stronger for:
- concept familiarity;
- recall-oriented concept proficiency;
- early confidence growth.

Weaker for:
- mock readiness;
- answer defense under follow-up.

### Practice
Stronger for:
- transfer;
- decomposition;
- trade-off reasoning;
- applied concept confidence.

Moderate for:
- mock readiness.

### Mock Interview
Strongest for:
- mock readiness;
- structured articulation;
- answer defense under follow-up;
- communication under pressure.

It may still update concepts, but concept refinement is not its main purpose.

## Event-specific update rules

### `evaluation_attached`
Effects:
- primary update of concept `proficiency_estimate` for bound concepts;
- primary update of subskill `proficiency_estimate` for rubric-bound subskills;
- modest growth of `confidence` when evidence is complete and session state is stable.

Weight modifiers:
- lower weight when many hints were used;
- lower weight when `answer_revealed` occurred;
- higher weight in `Practice` and `Mock Interview` for applied subskills;
- concept-specific positive updates from a single mock attempt should remain
  conservative even when the overall result is decent;
- lower confidence when transcript is partial or session ended unresolved.

Interpretation rules:
- for scenario-backed mock units, concept-level updates should come from
  explicit concept-specific downstream signals emitted by evaluation, not from
  family-level score or `bound_concept_ids` alone;
- absence of a concept-specific signal means no concept update for that concept;
- negative concept evidence may be easier to emit than strong positive concept
  evidence when the transcript is partial or ambiguous.

### `hint_requested`
Effects:
- increases concept `hint_dependency_signal` for relevant targets;
- dampens the weight of subsequent positive performance evidence;
- slows confidence growth.

Non-effect:
- should not directly collapse `proficiency_estimate`.

Interpretation rule:
A supported success is still success, but weaker evidence than an independent success.

### `answer_revealed`
Effects:
- strongly increases `hint_dependency_signal`;
- increases `review_due_risk` for relevant targets;
- lowers confidence in independent recall/performance;
- may slightly reduce `proficiency_estimate`, but should not be treated as catastrophic failure.

Interpretation rule:
Reveal indicates support need, not absolute inability.

### `follow_up_answered`
Effects:
- strongly updates subskills:
  - `tradeoff_reasoning`
  - `structured_articulation`
  - `answer_defense_under_followup`
  - `failure_mode_awareness`
- can moderately refine concept estimates when the follow-up is concept-specific.
- materially increases `mock_readiness_estimate` when follow-up performance is strong in `Practice` or `Mock Interview`.

Interpretation rule:
Follow-up performance updates subskills more strongly than raw concepts.

### `session_abandoned`
Effects:
- increases `recent_abandonment_signal`;
- increases `recent_fatigue_signal`;
- may slightly reduce confidence for unresolved targets;
- can increase `review_due_risk` when the learner repeatedly leaves the same area unfinished.

Non-effect:
- should not be treated as direct knowledge failure.

Interpretation rule:
Abandonment affects trajectory state more than knowledge state.

### `session_completed`
Effects:
- stabilizes the reliability of collected evidence;
- supports confidence growth when paired with meaningful evaluation;
- may slightly reduce fatigue signal after smooth completions.

Non-effect:
- completion alone does not directly increase proficiency.

## Confidence rules

Confidence should grow from:
- repeated meaningful attempts;
- completed sessions;
- moderately consistent evidence across time;
- evidence observed in more than one mode when available.

Confidence should be damped by:
- sparse evidence;
- heavy support use;
- reveal usage;
- repeated unresolved abandonment.

Rule:
Unknown must remain distinct from weak. Sparse negative evidence should not be over-interpreted as confirmed weakness.

## Review-due risk rules

`review_due_risk` should grow from:
- time since last successful retrieval or application;
- fragile performance;
- reveal usage;
- repeated support-dependent success.

`review_due_risk` should decrease from:
- recent successful independent retrieval;
- recent successful applied use in `Practice`;
- completed review-oriented sessions.

Rule:
Review due risk is driven by time plus fragility, not by time alone.
Time-sensitive review-due evaluation should therefore be anchored to current
wall-clock time when the profile is rebuilt.

## Mock-readiness rules

`mock_readiness_estimate` should rise when the learner shows:
- repeated acceptable performance in `Practice`;
- strong follow-up handling;
- good structure and communication;
- moderate/high confidence across relevant concepts and subskills.

It should stall or fall when the learner shows:
- high hint dependency;
- strong concept recall but weak defense under follow-up;
- repeated abandonment near scenario or mock tasks;
- low confidence despite isolated decent scores.

## Anti-goals for v1

Do not:
- implement opaque or model-only learner-state updates;
- infer strong weakness from a single bad event;
- treat hint use as hard failure;
- rely on low-level UI exhaust for learner-state updates;
- smear one scenario-family outcome across every bound concept;
- build per-card-type or per-scenario state maps in v1.

## Summary rules

1. `evaluation_attached` is the primary proficiency update event.
2. `hint_requested` dampens evidence and increases dependency, but does not equal failure.
3. `answer_revealed` is a stronger support-needed signal than hint use.
4. `follow_up_answered` updates defense/articulation/trade-off subskills strongly.
5. `session_abandoned` updates fatigue/abandonment more than knowledge.
6. Mode weighting is required.
7. Confidence grows from repeated completed evidence, not a single strong performance.
8. Scenario-backed mock concept updates require explicit evaluator-emitted
   concept signals; `bound_concept_ids` alone is not learner evidence.
