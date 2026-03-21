# Slice 016: Concept-Specific Mock Feedback

## Status

- completed

## Execution posture

`016` is the semantic follow-up after completed `015a`, `015b`, and `015c`.

Purpose:
- restore honest concept-level post-mock targeting after the conservative
  rollback in `015a`
- keep the fix aligned with bounded-context ownership from the v2.2 baseline
- make mock outcomes influence canonical concept state only through explicit,
  auditable evaluation signals

This slice is not a breadth expansion.
It should complete the deferred semantic direction from `015` without
reopening runtime or UI design.

## Goal

Allow reviewed `MockInterview / ReadinessCheck` outcomes to update bound
concepts in a concept-specific way that is semantically defensible, instead of:
- smearing one coarse scenario score across every bound concept, or
- dropping concept-level follow-up entirely

Expected outcome:
- evaluation emits explicit per-concept downstream signals for the bounded
  `URL Shortener` scenario family
- learner projection updates only the concepts that received explicit signals
- recommendation can propose post-mock remediation tied to the actually weak
  concept, not to the whole scenario family
- the system still avoids per-scenario learner-state maps

## Why this slice exists

After `015a`:
- `bound_concept_ids` is validated and safe
- mock outcomes still update `subskill_state` and `trajectory_state`
- concept-level post-mock targeting was intentionally rolled back

That rollback made the branch honest, but left one deferred capability:
- `URL Shortener` mock work cannot yet drive concept-specific follow-up through
  canonical concept state

The binding docs already imply a better direction:
- `evaluation_engine_v1.md` requires normalized `downstream_signals`
- `learner_state_update_rules_v1.md` says `evaluation_attached` is the primary
  proficiency update event for bound concepts
- `implementation_mapping_v1.md` keeps evaluation, projection, and
  recommendation responsibilities separate

`016` exists to restore that path without violating those seams.

## Affected bounded contexts

- `evaluation_engine`
- `learner_projection`
- `recommendation_engine`
- narrow binding support in `content_kernel` / `learning_design`

## Non-goals

- no second scenario family in this slice
- no new runtime state or follow-up behavior
- no frontend redesign
- no per-scenario learner-state map
- no generic model-only concept inference
- no authoring-framework redesign beyond what is strictly needed for the
  binding contract

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- keep `evaluation_attached` as the primary concept-update event
- keep recommendation selecting structured learning actions, not raw evaluator
  outputs
- keep `bound_concept_ids` as a bounded allowed-concept set, not as sufficient
  evidence by itself
- keep concept-specific mock feedback deterministic and explainable
- do not infer confirmed weakness from a single coarse family-level score

## Hidden assumptions to lock before code

- `URL Shortener` remains the only scenario family in scope
- concept-specific mock signals should be emitted by `evaluation_engine`, not
  derived heuristically inside `learner_projection`
- `bound_concept_ids` constrains which concepts a scenario may update, but does
  not by itself define signal strength
- a single mock attempt may update more than one bound concept, but only when
  evidence is explicit enough to justify it
- weak mock evidence must remain distinct from unknown or unobserved concepts

## Architectural approaches considered

### Option A: Projection-owned translation from coarse scenario results

Shape:
- keep evaluator output mostly as-is
- let `learner_projection` translate scenario-family results and
  `bound_concept_ids` into concept updates

Pros:
- smaller evaluator diff
- fewer new output fields

Cons:
- violates bounded-context ownership from
  `docs/03_architecture/implementation_mapping_v1.md`
- pushes scenario-specific semantic interpretation into projection
- risks repeating the same smear problem under a more complicated heuristic

### Option B: Evaluator-owned per-concept downstream signals

Shape:
- extend the scenario-family evaluation binding so evaluator emits explicit
  concept-targeted downstream signals
- projection consumes those signals without inventing its own scenario
  heuristics
- recommendation reads the resulting projection state

Pros:
- aligns with `evaluation_engine_v1.md` and `learner_state_update_rules_v1.md`
- keeps scenario interpretation inside `evaluation_engine`
- gives recommendation a defensible concept-level surface

Cons:
- requires a slightly richer binding contract
- likely needs source-of-truth doc updates before code

## Recommendation

Choose Option B.

Reasoning:
- the core missing contract is not "how to rank recommendations", but "who is
  allowed to interpret scenario evidence into concept meaning"
- docs already point to evaluator-emitted downstream signals as the correct
  ownership seam
- projection should remain a consumer of normalized signals, not a
  scenario-family reasoning engine

## Frozen decisions before code

### Binding ownership decision

The concept-signal mapping for `016` lives in the scenario-family binding
surface, not:
- in `content_schema`
- in author-supplied per-scenario heuristic notes
- in `learner_projection`

Primary contract home:
- `docs/03_architecture/scenario_rubric_binding_v1.md`

Reasoning:
- `bound_concept_ids` remains the allowed-concept set
- family-specific evidence interpretation belongs with evaluation binding
- projection should consume normalized signals, not invent family semantics

### Downstream signal shape

`016` should lock one explicit evaluator output shape for concept-specific mock
evidence:

- `signal_type = concept_mock_evidence`
- `concept_id`
- `direction` (`positive` or `negative`)
- `signal_strength` as a normalized scalar in `[0.0, 1.0]`
- `signal_confidence` as a normalized scalar in `[0.0, 1.0]`
- `source_criteria[]`
- `evidence_basis[]`

`evidence_basis[]` should use bounded labels such as:
- `explicit_coverage`
- `explicit_gap`
- `gating_failure`
- `expected_cue_present`
- `expected_cue_missing`

Rules:
- no free-form prose-only downstream signal
- no concept signal without a concrete `concept_id`
- no concept signal for concepts outside the scenario's `bound_concept_ids`
- prose review remains separate from normalized learner-model inputs

### Conservative positive-signal rule

`016` should not treat one mock attempt as strong positive concept mastery.

Frozen posture:
- negative concept signals may be emitted from explicit gaps, required-cue
  absence, or relevant gating failure
- positive concept signals require explicit observed evidence for that concept
  and should not be emitted from vague overall success
- a single reviewed mock attempt may emit at most a moderate positive signal
  for a concept; projection should not interpret one mock as high-confidence
  mastery
- when evidence is partial or ambiguous, prefer no positive concept signal

### First-pass implementation stance

`016` should land as `negative-first`.

Meaning:
- explicit negative concept signals are required for slice completion
- positive concept signals remain allowed by the contract, but are not required
  for the first implementation pass
- recommendation and summary acceptance gates should depend only on
  concept-specific weakness, not on concept-specific reinforcement

Reasoning:
- post-mock remediation is the highest-value recovery path reopened by `016`
- negative concept signals are easier to justify from explicit gaps and gating
  failures
- deferring positive concept reinforcement keeps the first pass narrow and
  avoids over-claiming mastery from one reviewed mock

### Recommendation follow-up decision

`016` restores concept-specific post-mock targeting with a conservative action
policy:

- primary follow-up target after concept-specific mock weakness:
  `Practice / Remediate`
- fallback when the policy envelope suppresses stricter remediation due to low
  confidence, fatigue, or abandonment pressure:
  `Study / Reinforce`
- `016` should not re-open immediate `MockInterview` escalation as the default
  response to a weak mock concept signal

Recommendation envelope for the first pass:
- choose `Practice / Remediate` when:
  - a recent concept-specific negative mock signal exists,
  - the policy envelope does not suppress remediation severity,
  - and the learner is not blocked by immediate fatigue/abandonment guardrails
- fall back to `Study / Reinforce` when:
  - the negative concept signal exists but confidence is still low, or
  - the completion-likelihood envelope makes `Practice / Remediate` too harsh

## Proposed implementation shape

### 1. Extend the scenario-family binding with concept-signal rules

Behavior:
- for `binding.url_shortener.v1`, define explicit rules for when evaluation may
  emit concept-specific signals for:
  - `concept.url-shortener.id-generation`
  - `concept.url-shortener.storage-choice`
  - `concept.url-shortener.read-scaling`
  - `concept.url-shortener.caching`

Rules:
- concept-signal rules remain family-specific and deterministic
- emitted concept ids must be a subset of the scenario's `bound_concept_ids`
- this slice should not require a second author-managed mapping field if the
  family binding can carry the semantics honestly

### 2. Make evaluator emit explicit per-concept downstream signals

Behavior:
- evaluation produces normalized `downstream_signals`; the first pass of `016`
  requires concept-specific negative evidence, and may omit positive concept
  evidence unless it is explicit enough to justify it conservatively
- evaluator does not emit concept signals for unobserved or ambiguous areas

Rules:
- criterion-level and cue-level evidence remain distinct from prose summary
- concept-specific weakness must be justified by explicit evidence or explicit
  required-cue absence
- low weighted score alone is insufficient to emit a concept-specific signal
- low-confidence evaluations should dampen concept-signal strength
- positive concept signals must follow the conservative positive-signal rule

### 3. Update learner projection to consume explicit concept signals only

Behavior:
- `learner_projection` updates `concept_state` only from emitted concept
  signals, not from family-level heuristics
- mock outcomes continue to update `subskill_state` and `trajectory_state` as
  today

Rules:
- no raw `scenario.*` ids may appear in `concept_state`
- absence of a concept-specific signal means "no concept update", not
  automatic weakness
- unknown must remain distinct from weak

First-pass update rule:
- projection should use scalar weighting rather than discrete bands
- effective signal weight:
  `effective_weight = signal_strength * signal_confidence * mode_weight * independence_weight`
- `mode_weight` for mock concept refinement should remain moderate relative to
  mock subskill/readiness updates
- `independence_weight` should be damped by hint/reveal dependence using the
  existing conservative support posture
- first-pass acceptance only requires negative concept deltas; if positive
  deltas are implemented, they must stay smaller and more confidence-limited
  than comparable negative updates from explicit gaps

### 4. Restore truthful post-mock concept targeting in recommendation

Behavior:
- recommendation may choose concept-level remediation after a reviewed mock
  when projection shows actual concept-specific weakness
- recommendation should not broaden that targeting to unrelated bound concepts

Rules:
- guardrails from `013c`, `014`, and `015c` remain in place
- immediate re-mock suppression remains orthogonal and must stay intact
- rationale should explain the specific concept follow-up in terms of recent
  mock evidence, not raw scenario ids
- primary concept-level follow-up should be `Practice / Remediate`, with
  `Study / Reinforce` only as a policy-envelope fallback

### 5. Keep learner summary effects conservative

Behavior:
- concept-specific mock weakness may appear immediately in weak-area surfaces
- review-due promotion should still depend on the existing recency/fragility
  rules rather than on "came from a mock" alone

Rules:
- `016` should not auto-promote every mock-derived weak concept into
  `review_due`
- learner-facing summary must stay aligned with the same projection semantics
  used by recommendation

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_rule_first_evaluator.py`
  Evaluator emits explicit concept-specific downstream signals for
  `binding.url_shortener.v1` only when evidence justifies them, with
  negative-first acceptance semantics.
- `backend/tests/test_learner_projection.py`
  Projection updates only the concepts that received explicit evaluator signals
  and leaves unrelated bound concepts untouched, using scalar weighting from
  `signal_strength` and `signal_confidence`.
- `backend/tests/test_recommendation_engine.py`
  Post-mock follow-up targets the actually weakened bound concept instead of
  the whole scenario family, with `Practice / Remediate` as the primary
  action and `Study / Reinforce` only as a bounded fallback.
- `backend/tests/test_learner_summary.py`
  Learner-facing weak/review-due surfaces reflect real concept-specific mock
  evidence without leaking scenario ids or unrelated concepts.

### Phase 1. Binding and evaluator output

Lock tests that prove:
- a weak `id generation / collision avoidance` result emits a negative signal
  for `concept.url-shortener.id-generation`, not for every bound concept
- weak `storage choice for short id -> long URL` emits a negative signal for
  `concept.url-shortener.storage-choice`
- weak `redirect/read path scaling` emits a negative signal for
  `concept.url-shortener.read-scaling`
- cache placement evidence may update `concept.url-shortener.caching` only when
  the transcript actually addresses it
- evaluator does not emit concept signals outside the scenario's
  `bound_concept_ids`
- evaluator does not emit a concept-specific negative signal from low weighted
  score alone without explicit gap, cue absence, or gating relevance
- evaluator does not emit a positive concept signal from vague overall success
  without explicit evidence for that concept

### Phase 2. Projection consumption

Lock tests that prove:
- explicit concept signals update only the named concepts
- unrelated bound concepts keep their previous state
- mock subskill and trajectory updates from `013c` remain intact
- low-confidence concept signals are damped rather than over-interpreted
- scalar weighting uses both `signal_strength` and `signal_confidence`
- absence of a positive concept signal does not block the negative-first
  remediation path

### Phase 3. Recommendation and summary

Lock tests that prove:
- after a reviewed mock with concept-specific weakness, recommendation selects
  `Practice / Remediate` on the actually weakened concept when policy envelope
  allows it
- when the same concept signal is weak but confidence/fatigue envelope blocks
  remediation severity, recommendation falls back to `Study / Reinforce`
- recommendation does not target the whole bound concept set by default
- learner summary surfaces show the specific weak concept without leaking raw
  scenario ids
- learner summary does not auto-mark every mock-derived weak concept as review
  due unless existing fragility/recency rules justify it
- immediate re-mock suppression and fatigue guardrails still behave as before

## Acceptance criteria

- `evaluation_engine` emits concept-specific downstream signals for the bounded
  `URL Shortener` family
- explicit negative concept signals are sufficient to complete the first pass;
  positive concept signals remain optional and conservative
- `learner_projection` updates only explicitly signaled concepts
- `recommendation_engine` can produce truthful post-mock concept-level
  remediation without broad bound-concept smear
- the new behavior remains conservative: negative concept signals are easier to
  emit than strong positive ones
- no per-scenario learner-state map is introduced
- existing `013c`, `014`, `015a`, `015b`, and `015c` guardrails remain intact

## Weak spots and undefined areas

- the mapping from scenario-family evidence to concept-specific signals is the
  main load-bearing contract; if it remains too implicit, `016` should stop and
  formalize that contract before implementation
- coarse criterion ids alone may be insufficient; some signals will need to be
  anchored to explicit expected evidence cues or gating conditions
- positive signals are easier to over-claim than negative ones; tests should
  prefer conservative updates when evidence is partial
- if implementing this slice requires a new author-managed schema field rather
  than a family-binding extension, source-of-truth docs must be updated first
  and the slice should not proceed as a "code-only" change

## Source-of-truth review before code

Review and update as needed:
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`

Potentially unchanged if the binding remains family-owned rather than
author-schema-owned:
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`

Current expectation:
- no ADR should be required if `016` remains a bounded extension of the
  existing evaluation -> learner -> recommendation contract
- source-of-truth doc updates are likely required before or during
  implementation, because `016` introduces a richer downstream-signal contract

Execution gate:
- do not start code changes until the downstream-signal shape and binding
  ownership decision are either reflected in the source-of-truth docs above or
  explicitly confirmed unchanged by a narrow doc review

## Exit condition

`016` is complete when a reviewed `URL Shortener` mock attempt can drive
concept-specific learner-state updates and truthful post-mock remediation
without violating the v2.2 baseline or collapsing bounded-context seams.
