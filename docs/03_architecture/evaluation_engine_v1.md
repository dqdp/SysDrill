# Evaluation Engine v1

## Purpose

Оценивать ответы пользователя так, чтобы результат был:
- достаточно строгим для interview prep;
- explainable и auditable;
- пригодным для downstream learner model и recommendation;
- устойчивым к drift в pure freeform LLM judgment.

## Core principle

**Rubric first, binding second, model third.**

1. Global rubric schema defines available criteria.
2. Scenario/card binding defines applicability, weights, mode adjustments, and gating.
3. Rules and model-assisted logic fill criterion results.
4. Aggregation produces normalized downstream signals.

Это защищает систему от деградации в режим
"модель просто решила, что это 7/10".

## Required dependencies

Evaluation Engine depends on:
- `docs/04_content/rubric_schema.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/03_architecture/concept_recall_binding_v1.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`

Без них scoring считается underspecified.

## Contract boundary

## Inputs
`EvaluationRequest` should include at least:
- `session_id`
- `session_mode`
- `session_intent`
- `executable_unit_id`
- `unit_family` / `scenario_family`
- `binding_id`
- `transcript_ref` or normalized transcript text
- `hint_usage_summary`
- `answer_reveal_flag`
- `timing_summary`
- `completion_status`
- `content_version_refs`
- `strictness_profile`

Prototype note:
- the first manual reviewed implementation path may use
  `unit_family = concept_recall` together with `binding.concept_recall.v1`
- this is a bounded prototype seam, not a replacement for the scenario-family
  evaluation surface

## Outputs
`EvaluationResult` should include at least:
- `evaluation_id`
- `session_id`
- `unit_id`
- `criterion_results[]`
- `gating_failures[]`
- `weighted_score`
- `overall_confidence`
- `missing_dimensions[]`
- `review_summary`
- `downstream_signals`
- `rubric_version_ref`
- `binding_version_ref`
- `evaluation_mode` (`rule_only`, `llm_assisted`, `hybrid`)
- `evaluator_version_ref`

## Criterion result contract
Each criterion result should contain:
- `criterion_id`
- `applicability`
- `score_band`
- `weight_used`
- `observed_evidence[]`
- `missing_aspects[]`
- `inferred_judgment`
- `criterion_confidence`
- optional `gating_status`

Rule:
evidence and judgment must remain distinct.

## Execution pipeline

## Step 1 — Build evaluation context
Assemble a normalized context from:
- mode and intent
- executable unit metadata
- scenario/card family
- strictness profile
- transcript completeness
- support usage summary
- abandon / partial flags

Output:
`EvaluationContext`

## Step 2 — Rule-based extraction
Extract and persist **observable signals**, such as:
- coverage of expected dimensions
- presence/absence of key constraints
- mention of storage / scaling / reliability elements
- definition / usage-fit / trade-off cues for concept-recall units
- support usage and reveal depth
- abandonment or truncation indicators

Goal:
collect observed evidence before attempting higher-level judgment.

Output:
`ObservedSignalBundle`

## Step 3 — Model-assisted interpretation
Use model assistance only for criteria that genuinely require interpretation, such as:
- coherence
- explanatory strength
- trade-off depth
- whether the answer materially addresses the task

Restrictions:
- model assistance may not silently bypass binding-defined gating
- model assistance may not fabricate evidence
- model assistance must return low-confidence judgments when transcript quality is poor

Output:
`InterpretationBundle`

## Step 4 — Criterion assembly
For each applicable criterion:
- merge observed signals and interpreted judgment
- attach `score_band`
- attach `criterion_confidence`
- attach `missing_aspects`
- attach evidence snippets

Output:
`CriterionResult[]`

## Step 5 — Binding application
Apply binding-defined:
- applicability
- weights
- mode adjustments
- strictness adjustments
- gating rules

Output:
`BoundCriterionResult[]`

## Step 6 — Aggregation and normalization
Compute:
- weighted score
- gating failures
- overall confidence
- downstream learner-model signals

Important rule:
aggregation may merge rule signals and model-assisted signals, but may not suppress hard gating failure.

Output:
`EvaluationAggregate`

## Step 7 — Review material generation
Produce:
- strengths
- missed dimensions
- shallow reasoning areas
- next-focus suggestions
- support-dependence notes where relevant

Output:
`ReviewSummary`

## Scoring and confidence semantics

## Weighted score
Weighted score is a normalized summary for:
- dashboarding
- coarse trend analysis
- recommendation support

It is **not** the only truth of the evaluation result.
Criterion-level outputs remain primary.

## Overall confidence
Overall confidence should be derived from:
- transcript completeness
- criterion coverage
- support leakage level
- model certainty where applicable
- whether answer length plausibly matches task scope

Low confidence means:
- evaluation still returns a result;
- learner state updates should discount it;
- recommendation should avoid overcorrecting from a single weak observation.

## Downstream signals
Evaluation must emit normalized downstream signals, not just prose.
Examples:
- `concept_support_dependence`
- `subskill_tradeoff_reasoning_strength`
- `followup_defense_weakness`
- `review_due_fragility`
- `mock_readiness_support`

These signals are inputs to learner-state projection, not direct state mutations.

### Concept-specific mock downstream signals
For scenario-backed mock units, evaluation may emit explicit concept-specific
downstream signals when the scenario-family binding defines them.

Required shape:
- `signal_type` (`concept_mock_evidence`)
- `concept_id`
- `direction` (`positive` or `negative`)
- `signal_strength` in `[0.0, 1.0]`
- `signal_confidence` in `[0.0, 1.0]`
- `source_criteria[]`
- `evidence_basis[]`

Recommended bounded `evidence_basis[]` labels:
- `explicit_coverage`
- `explicit_gap`
- `gating_failure`
- `expected_cue_present`
- `expected_cue_missing`

Rules:
- mapping from scenario evidence to concept-specific signals is owned by the
  scenario-family binding, not by `learner_projection`
- emitted `concept_id` must remain within the scenario's allowed concept set;
  when `bound_concept_ids` exists, concept signals must be a subset of it
- negative signals may be emitted from explicit gaps, gating failures, or
  explicit expected-cue absence
- positive signals require explicit observed evidence for that concept and must
  remain conservative from a single attempt
- absence of a concept-specific signal means no concept update for that concept
- prose review summary may explain the result, but may not replace the
  normalized downstream signal contract

## Mode handling

### Study
- lower strictness
- more tolerance for partial answer coverage
- emphasis on formative feedback
- concept signals usually stronger than readiness signals

### Practice
- medium strictness
- applied reasoning and dimension coverage matter more
- concept and subskill signals both flow downstream

### Mock Interview
- highest strictness in v1
- lower tolerance for missing primary dimensions
- communication clarity, structured articulation, and follow-up defense become load-bearing
- mock-readiness downstream signals become strong

## Support handling

### Hint usage
- does not equal failure
- lowers independence interpretation
- dampens effective downstream strength of positive performance

### Answer reveal
- stronger support-needed signal than hints
- should materially lower independent-completion confidence
- may raise review fragility / review-due signals

### Partial / abandoned attempts
- produce conservative, lower-confidence results
- must not be treated as full negative knowledge proof
- should attach trajectory-relevant signals

## Evidence quality rules

1. Evidence snippets must point to what is actually present in the answer.
2. Paraphrase may summarize, but may not imply the learner said what they did not say.
3. Judgment without evidence is allowed only as low-confidence auxiliary commentary.
4. Empty or truncated transcript cannot receive high-confidence criterion coverage.
5. Non-applicable criteria must remain explicitly non-applicable, not silently scored.

## Failure handling

### Evaluation input incomplete
- emit degraded-confidence evaluation
- persist failure note
- allow retry if infrastructure issue, not learner issue

### Model-assist unavailable
- fall back to rule-dominant or degraded evaluation mode
- preserve explicit `evaluation_mode`
- do not hide the degraded path

### Binding/rubric mismatch
- fail closed
- do not emit misleading full result
- raise a contract issue for operators

## Audit and testing requirements

Evaluation outputs must support:
- criterion-level replay/review
- comparison across model/evaluator versions
- consistency checks for near-duplicate answers
- scenario-binding enforcement checks
- support-effect tests

Authoritative QA plan:
- `docs/05_ops/evaluation_quality_plan_v1.md`

## Anti-patterns

- one total score without criterion results
- freeform model judgment without rubric binding
- no evidence snippets
- hard failure hidden inside summary prose
- high-confidence scoring from partial transcript
- downstream learner update that ignores evaluation confidence
- mixing evidence extraction and judgment so they cannot be audited separately
