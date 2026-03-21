# Recommendation Engine Surface

## Purpose

This document defines the **stable policy surface** for the recommendation subsystem.
It exists so that v1 can use a deterministic policy engine while later versions may replace or augment candidate scoring with a model-backed implementation without changing the rest of the system.

## Design goal

Keep the following stable across deterministic and future model-assisted versions:
- input context shape
- bounded action space
- decision output shape
- guardrail layer
- decision logging requirements

## Stable input: RecommendationContext

`RecommendationContext` should include:
- learner concept state summary
- learner subskill state summary
- learner trajectory state summary
- recent recommendation history ordered by actual acceptance time
- recent session outcomes ordered by actual review/evaluation time
- review due items
- available action templates
- policy constraints
- current policy version metadata

## Stable intermediate surface: CandidateAction[]

Candidate actions must be generated inside a bounded action space.
A model may later score candidates, but it should not invent action types outside that space.

Candidate action fields:
- `mode`
- `session_intent`
- `target_type`
- `target_id`
- `difficulty_profile`
- `strictness_profile`
- `session_size`
- optional `delivery_profile`

## Stable output: RecommendationDecision

`RecommendationDecision` should include:
- `decision_id`
- `policy_version`
- `decision_mode` (`rule_based`, later `model_assisted`, `hybrid`)
- `candidate_actions`
- `chosen_action`
- `supporting_signals`
- `blocking_signals`
- `rationale`
- optional `alternatives_summary`

## Guardrail layer

The following should remain deterministic even after model-assisted ranking is introduced:
- candidate validity rules
- hard anti-loop constraints
- fatigue caps
- mock-readiness gates
- illegal-action rejection

## Future extension points

Possible future model-assisted replacements:
- candidate scoring
- tie-breaking / ranking refinement
- exploration scheduling

Possible future hybridization:
- deterministic candidate generation
- model-assisted ranking
- deterministic guardrail enforcement
- deterministic logging and rationale envelope

## Non-goal

This surface does not prescribe a specific model architecture.
It only preserves the system contract required to plug one in later without destabilizing the surrounding architecture.
