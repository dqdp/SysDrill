# Recommendation Decision Logging and Offline Evaluation

## Purpose

Recommendation decisions should be logged in a way that supports:
- debugging
- assurance
- offline evaluation
- future model-assisted policy development

## Required decision log fields

Each logged decision should include:
- `decision_id`
- `policy_version`
- `decision_mode`
- `context_snapshot_ref` or compact context summary
- `candidate_actions`
- `chosen_action`
- `supporting_signals`
- `blocking_signals`
- `rationale`
- `created_at`

## Follow-up outcome linkage

Later outcome linkage should capture at least:
- whether the recommendation was shown
- whether it was accepted or skipped
- whether the resulting session completed
- whether the resulting session was abandoned
- summary of evaluation quality from the resulting action

## Offline evaluation goals

The logged data should allow later analysis of:
- action acceptance rate
- action completion rate
- action usefulness by type
- over-remediation loops
- escalation quality
- outcome differences between deterministic and future model-assisted ranking

## Counterfactual-friendly posture

Where practical, the system should preserve at least a compact summary of viable alternatives so that later evaluation can ask:
- what was chosen
- what else was available
- why it was not chosen

## Non-goal

This document does not define the production ranking algorithm. It defines the evidence surface needed to evaluate it over time.
