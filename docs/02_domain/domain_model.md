# Domain Model

## Purpose
This document defines the main domain entities and their invariants. It is intentionally storage-agnostic.

## Content Kernel entities
### Concept
Fields:
- `id`
- `title`
- `description`
- `why_it_matters`
- `when_to_use`
- `tradeoffs`
- `related_concepts`
- `prerequisites`
- `canonical_examples`
- `anti_patterns` (optional)
- `common_misconceptions` (optional)

### Pattern
Fields:
- `id`
- `name`
- `problem_it_solves`
- `typical_components`
- `strengths`
- `weaknesses`
- `failure_modes`
- `related_concepts`

### Scenario
Fields:
- `id`
- `title`
- `prompt`
- `content_difficulty_baseline`
- `expected_focus_areas`
- `hidden_constraints` (optional)
- `canonical_axes`
- `canonical_follow_up_candidates`
- `reference_patterns` (optional)
- `anti_shortcuts` (optional)

### HintLadder
Fields:
- `id`
- `content_id`
- `levels`
- `disclosure_policy_note` (optional)

## Learning Design entities
### Card
Fields:
- `id`
- `card_type`
- `targets`
- `pedagogical_goal`
- `prompt_frame`
- `difficulty_transform`
- `allowed_modes`
- `hint_policy_ref`
- `completion_rule_ref`

### ExerciseTemplate
Fields:
- `id`
- `template_type`
- `target_entity_types`
- `expected_response_shape`
- `follow_up_policy`
- `evaluation_binding_strategy`
- `default_strictness`

### ExecutableLearningUnit
Fields:
- `id`
- `source_content_ids`
- `mode`
- `session_intent`
- `visible_prompt`
- `pedagogical_goal`
- `effective_difficulty`
- `allowed_hint_levels`
- `follow_up_envelope`
- `completion_rules`
- `evaluation_binding_id`

## Session Runtime entities
### Session
Fields:
- `id`
- `user_id`
- `mode`
- `session_intent`
- `strictness_profile`
- `planned_units`
- `current_state`
- `started_at`
- `ended_at`
- `completion_state`

### Turn
Fields:
- `id`
- `session_id`
- `unit_id`
- `turn_state`
- `prompt_shown_at`
- `answer_submitted_at`
- `follow_up_index`
- `hint_usage`

### UserAnswer
Fields:
- `id`
- `turn_id`
- `transcript`
- `submission_boundary`
- `timing_signals`
- `attachments` (optional)

## Evaluation entities
### RubricTemplate
Fields:
- `rubric_id`
- `criteria_catalog`
- `score_bands`
- `criterion_result_schema`
- `aggregation_rules`

### ScenarioRubricBinding
Fields:
- `binding_id`
- `scenario_family`
- `required_criteria`
- `secondary_criteria`
- `not_applicable_criteria`
- `criterion_weights`
- `gating_conditions`
- `mode_adjustments`

### CriterionResult
Fields:
- `criterion_id`
- `applicability`
- `weight`
- `score_band`
- `observed_evidence`
- `missing_aspects`
- `inferred_judgment`
- `criterion_confidence`

### EvaluationResult
Fields:
- `evaluation_id`
- `rubric_version`
- `binding_id`
- `criterion_results`
- `weighted_score`
- `gating_failures`
- `overall_confidence`
- `summary_feedback`
- `downstream_signals`

### ReviewReport
Fields:
- `session_id`
- `strengths`
- `missed_dimensions`
- `reasoning_gaps`
- `recommended_next_focus`
- `linked_evaluation_ids`

## Learning Intelligence entities
### InteractionEvent
Append-only fact of user or system interaction.

### SkillEstimate
Fields:
- `skill_id`
- `proficiency_estimate`
- `confidence`
- `review_due_risk` (concept-oriented, optional)
- `hint_dependency_signal` (concept-oriented, optional)
- `evidence_count`
- `recent_trend`
- `last_evidence_at`

### LearnerTrajectoryState
Fields:
- `recent_fatigue_signal`
- `recent_abandonment_signal`
- `mock_readiness_estimate`
- `mock_readiness_confidence`
- `last_active_at`

### LearnerProfile
Projection of interaction history into concept, subskill, and trajectory state.

### ReviewQueueItem
Fields:
- `id`
- `user_id`
- `target_id`
- `reason`
- `urgency`
- `due_at`
- `recommended_mode`
- `recommended_intent`

### RecommendationAction
Fields:
- `action_id`
- `mode`
- `session_intent`
- `target_type`
- `target_id`
- `difficulty_profile`
- `strictness_profile`
- `session_size`
- `delivery_profile`
- `rationale`

### RecommendationDecision
Fields:
- `decision_id`
- `user_id`
- `candidate_actions`
- `chosen_action`
- `rationale`
- `guardrail_flags`
- `timestamp`

## Relationships
- `Pattern` relates to multiple `Concept` entities.
- `Scenario` depends on multiple `Concept` and `Pattern` entities.
- `Card` and `ExerciseTemplate` transform content entities into executable units.
- `Session` contains a sequence of `Turn` entities.
- `Turn` produces `UserAnswer` and `InteractionEvent` records.
- `EvaluationResult` binds to `RubricTemplate` and `ScenarioRubricBinding`.
- `ReviewReport` aggregates one or more evaluation outputs.
- `LearnerProfile` is updated from `InteractionEvent` and `EvaluationResult`.
- `RecommendationDecision` selects a `RecommendationAction` from a bounded set.

## Invariants
1. Canonical content truth is independent from learner-specific state.
2. Learning Design may transform content, but must not silently change canonical meaning.
3. Session Runtime emits events and orchestrates sessions; it does not mutate learner state directly.
4. Evaluation must keep observed evidence separate from inferred judgment.
5. Recommendation decisions must be rationale-bearing and guardrail-aware.
6. `ReviewReport` and `ReviewQueueItem` influence follow-on planning, but do not create a separate top-level runtime mode.
