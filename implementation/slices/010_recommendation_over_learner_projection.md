# Slice 010: Recommendation Over Learner Projection

## Status

- completed

## Goal

Upgrade the current deterministic `recommendation_engine` so it consumes a real
`RecommendationContext` built from `learner_projection` rather than relying on
raw reviewed-outcome heuristics.

This slice should make recommendation more faithful to the documented v1 policy
without changing:
- the public recommendation API surface
- the frontend recommendation flow
- the runtime action-acceptance contract

## Affected bounded contexts

- `recommendation_engine`
- narrow consumption of `learner_projection`
- narrow consumption of `session_runtime`

## Non-goals

- no frontend or UX changes
- no learner dashboard API
- no new public learner profile API
- no model-assisted ranking
- no durable persistence changes
- no new runtime event families
- no mock-interview orchestration changes

## Constraints

- preserve v2.2 baseline and current bounded-context ownership
- recommendation still returns a structured learning action, not raw content
- public `RecommendationDecision` shape stays stable
- guardrails remain deterministic
- recommendation must consume `learner_projection` through explicit seams, not
  by re-implementing learner-state logic locally
- current runtime action space remains bounded by the implemented
  `concept_recall` units

## Known starting point

- `009` added a rebuild-on-read `LearnerProjector`
- the current `recommendation_engine` still drives policy from:
  - launchable action candidates
  - `list_user_reviewed_outcomes(user_id)`
  - recent accepted recommendation patterns
- current policy behavior is still bootstrap-oriented:
  - unseen concepts -> `Study / LearnNew`
  - weak outcomes -> `Practice / Remediate`
  - middling outcomes -> `Practice / Reinforce`
  - otherwise -> `Study / SpacedReview`

## Architectural approaches considered

### Option A: RecommendationEngine-owned context assembly

- inject or construct `LearnerProjector` inside `RecommendationEngine`
- build a narrow internal `RecommendationContext` on demand from:
  - learner profile
  - recent reviewed session outcomes
  - recent recommendation history
  - launchable action candidates
- keep context assembly and ranking in the existing module family

Trade-offs:
- minimal scope and fastest path to usable policy improvement
- preserves current public API and test harness
- provides a clean dependency-injection seam for tests
- still keeps some context-shaping logic inside `recommendation_engine`

### Option B: Separate RecommendationContextBuilder module

- introduce a distinct internal module just to assemble normalized context

Trade-offs:
- cleaner long-term decomposition
- more files and more seams right away
- broader than needed for the first projector-backed recommendation slice

### Option C: Keep recommendation bootstrap-only until dashboard/API work lands

- defer projector consumption and continue using raw reviewed outcomes

Trade-offs:
- no immediate policy migration risk
- wastes the new `learner_projection` seam
- leaves `010` without real bounded-context value

Decision:
- choose Option A

## Proposed implementation shape

- extend `RecommendationEngine` to accept an optional `LearnerProjector`
  dependency for testing and internal composition
- add an internal context assembly step that gathers:
  - `concept_state`
  - `subskill_state`
  - `trajectory_state`
  - latest reviewed outcomes per concept
  - review-due items
  - recent accepted recommendation patterns
  - currently launchable candidate actions
- preserve the public `next_recommendation(user_id)` signature
- keep `RecommendationDecision` shape unchanged

## Policy scope for 010

`010` is not trying to deliver the full final v1 policy. It should introduce
the first projector-backed behavior while staying honest about the current
action space and evidence quality.

### Required policy behavior

1. `Study / LearnNew` remains the default for truly unseen concepts.
2. `Practice / Remediate` is chosen only for sufficiently evidenced weakness,
   not merely sparse evidence.
3. `Practice / Reinforce` is preferred when evidence is emerging or when
   supported subskills are still weak despite concept familiarity.
4. `Study / SpacedReview` covers maintenance when there is no higher-priority
   weakness and no unseen exploration target.
5. anti-loop guardrails remain deterministic and operate on post-filter
   candidates.

### Deliberate limitations

- `MockInterview` remains out of candidate generation until the runtime action
  space supports it
- `recent_fatigue_signal` and `recent_abandonment_signal` may remain dormant
  because runtime does not yet emit the needed events
- `mock_readiness_*` may only be used conservatively as a gate/bias signal

## Internal RecommendationContext contract

The internal context assembled in `010` should include:
- `concept_state`
- `subskill_state`
- `trajectory_state`
- `latest_reviewed_outcomes_by_target`
- `review_due_targets`
- `candidate_records`
- `recent_accepted_patterns`
- `policy_version`

Rules:
- `RecommendationContext` remains internal in this slice; no public schema
  change is required
- context assembly must use `LearnerProjector`, not recompute learner state from
  scratch inside recommendation
- latest reviewed outcomes may still be carried alongside learner state for
  rationale text and tie-breaking, but not as a replacement for learner state

## Test contract

### 1. No learner evidence -> exploration

Given:
- no reviewed history for the user

Then:
- recommendation chooses `Study / LearnNew`
- practice actions for unseen concepts remain filtered out
- rationale and supporting signals reflect sparse evidence, not weakness

### 2. Confirmed weakness -> bounded remediation

Given:
- projector-backed concept state shows low proficiency with sufficient
  confidence for a seen concept

Then:
- recommendation chooses `Practice / Remediate`
- supporting signals reflect confirmed weakness rather than sparse evidence

### 3. Emerging evidence or weak supported subskill -> reinforcement

Given:
- concept familiarity is present but still unstable, or
- supported subskill evidence is weak enough to justify another bounded pass

Then:
- recommendation chooses `Practice / Reinforce`

### 4. Stable seen concept without urgent weakness -> maintenance review

Given:
- no unseen concepts remain
- no confirmed weakness outranks maintenance

Then:
- recommendation chooses `Study / SpacedReview`

### 5. Anti-loop guardrail still wins

Given:
- recommendation history would otherwise repeat the same pattern for a third
  time

Then:
- the repeated candidate is filtered post-context assembly
- `blocking_signals` includes `anti_loop_guardrail`

### 6. Recommendation actually consumes learner projection

Given:
- an injected projector returns a profile that conflicts with naive
  reviewed-outcome-only heuristics

Then:
- recommendation follows the projector-backed context

## Acceptance criteria

- `RecommendationEngine` consumes `LearnerProjector`
- projector-backed context assembly exists and is covered by tests
- public recommendation API shape stays unchanged
- current recommendation flow still passes existing backend/Frontend-adjacent
  assumptions
- policy behavior distinguishes unseen vs weak vs emerging vs maintenance using
  learner-state concepts rather than raw reviewed-outcome shortcuts
- anti-loop guardrail remains deterministic

## Weak spots review

- current projector supports only a partial subskill set, so `010` can only use
  those subskills honestly
- current runtime does not yet emit fatigue/abandonment/support events rich
  enough to activate all policy guardrails
- because action space is still concept-recall-only, recommendation may use
  richer context than it can fully express in action variety

## Hidden assumptions called out

- `LearnerProjector` output is stable enough to serve as the primary learner
  state input for recommendation in v1
- it is acceptable in `010` for recommendation to use both learner profile and
  latest reviewed outcomes, as long as learner profile remains the primary
  state summary
- frontend mocks that pin recommendation payloads do not constrain the backend
  policy version string tightly enough to block internal behavior changes

## Source-of-truth review

- `docs/00_change_protocol.md`: implementation slice only
- `docs/03_architecture/recommendation_policy_v1.md`: binding for policy
  posture
- `docs/03_architecture/recommendation_engine_surface.md`: public decision
  surface preserved
- `docs/03_architecture/learner_state_update_rules_v1.md`: respected via
  `learner_projection` input
- `docs/03_architecture/implementation_mapping_v1.md`: ownership preserved

## Change protocol expectations

- no ADR expected unless the slice needs a broader context-builder/persistence
  model
- source-of-truth docs should remain unchanged unless real contradictions appear
- v2.2 baseline should remain preserved
