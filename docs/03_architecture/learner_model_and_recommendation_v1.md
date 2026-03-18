# Learner Model and Recommendation v1

## Purpose
Learning Intelligence is a separate bounded context that turns semantic interaction history and evaluation outputs into learner state and next-action recommendations.

This file is an overview. Detailed rules live in:
- `learner_state_update_rules_v1.md`
- `recommendation_policy_v1.md`
- `recommendation_engine_surface.md`

## Responsibilities
- maintain evidence-weighted learner state
- keep concept, subskill, and trajectory projections
- track review due risk and support dependency
- choose the next structured learning action
- emit rationale-bearing recommendation decisions

## Non-responsibilities
- it does not score answers directly
- it does not own per-turn runtime orchestration
- it does not rewrite historical events or evaluations

## State model summary
The v1 learner model uses:
- `proficiency_estimate`
- `confidence`

It keeps three main state layers:
- concept state
- subskill state
- trajectory state

## Recommendation summary
Recommendation selects a bounded `RecommendationAction` containing:
- mode
- session intent
- target type and target id
- difficulty profile
- strictness profile
- session size
- rationale

The detailed policy remains deterministic in v1 and is maturity-aware, guardrail-heavy, and explainable.
