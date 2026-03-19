# Slice 007: Recommendation Placeholder

## Status

- planned

## Goal

Replace manual unit selection as the primary learner flow with a deterministic,
explainable next-step recommendation that preserves the documented bounded
contexts.

This slice should produce one bounded `RecommendationDecision` and allow runtime
to start from the chosen structured action without:
- folding recommendation logic into runtime orchestration
- pretending a full learner-projection subsystem already exists
- expanding beyond the currently implemented `concept_recall` prototype path

## Why this follows 006c

Milestone B is now demoable through a learner-visible frontend shell, but
current product feedback shows that the implemented `Practice` units are still
too close to `Study`. Recommendation should follow a narrow `Practice`
enrichment slice so that it ranks over a more meaningful bounded action space.

After `006c` is complete, the next critical path is to stop depending on manual
launcher choice for the main learner flow and to validate the documented
`Learning Intelligence -> Session Runtime` hand-off at a narrow, deterministic
level.

## In scope

- a backend `recommendation_engine` module family in the current monolith
- a deterministic bootstrap recommendation policy over the currently available
  bounded action space
- a recommendation API that returns one rationale-bearing decision
- a runtime entrypoint that starts a session from a recommendation action
- recommendation lifecycle events required for the placeholder flow
- thin frontend wiring to request and accept a recommendation instead of manual
  launch for the primary path

## Out of scope

- full learner-profile or learner-projection implementation
- durable recommendation storage across process restarts
- recommendation skip/explore UX beyond a minimal fallback
- dashboard surfaces, weak-area surfaces, or readiness surfaces
- `MockInterview` recommendation logic
- model-assisted ranking
- offline policy evaluation infrastructure

## Affected bounded contexts

- `recommendation_engine`
- narrow `web_api / ui`
- narrow `session_runtime` action-acceptance seam
- `interaction_event_model`

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/02_domain/hand_off_contracts.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/recommendation_engine_surface.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `implementation/roadmap.md`
- `implementation/status.md`

## Constraints

- recommendation must return a structured action, not a raw `unit_id`
- runtime must remain the owner of unit expansion/orchestration
- placeholder behavior must stay deterministic and rationale-bearing
- no recommendation action may target unsupported mode/intent pairs
- no learner-state mutation may bypass the append-only event/evaluation path
- current manual launcher may remain as a fallback/dev surface but should stop
  being the primary learner path

## Hidden assumptions

- there is no real learner projection yet, so `RecommendationContext` must be a
  narrow bootstrap context assembled from process-local runtime/evaluation facts
  plus available launchable actions
- because persistence is still process-local, recommendation history and
  completion signals reset on restart; the placeholder must not claim durable
  personalization
- current action targeting is effectively concept-level because the only
  implemented unit family is `concept_recall`

## Architectural approaches considered

### Option A: Separate deterministic recommendation engine plus runtime action acceptance

- implement a narrow recommendation service that assembles bootstrap context,
  generates candidate actions, ranks them deterministically, and returns a
  `RecommendationDecision`
- add a separate runtime endpoint that accepts the chosen action and expands it
  into the exact unit/session

Trade-offs:
- best match to `recommendation_engine -> session_runtime` contract
- keeps action ranking out of runtime
- requires a thin action-resolution seam in runtime
- still honest even with process-local bootstrap context

### Option B: Runtime-owned smart default start

- add runtime logic that picks a unit automatically when the learner clicks
  “continue”
- do not introduce a separate recommendation decision surface yet

Trade-offs:
- smallest amount of code
- directly violates the documented bounded-context split
- makes later recommendation extraction harder
- prevents explicit decision logging and rationale

Rejected because:
- it collapses recommendation into runtime orchestration

### Option C: Frontend-owned recommendation over launch options

- let the frontend inspect backend launch options and choose one with simple
  heuristics

Trade-offs:
- superficially fast
- violates the rule that UI does not own recommendation semantics
- creates an unversioned recommendation contract in the client

Rejected because:
- it puts policy logic in the wrong bounded context

Decision:
- choose Option A

## Proposed implementation shape

- add a new backend recommendation service that:
  - assembles a bootstrap `RecommendationContext`
  - generates bounded `RecommendationAction` candidates
  - ranks them deterministically
  - emits a versioned, rationale-bearing `RecommendationDecision`
- add a runtime action-acceptance entrypoint that:
  - accepts the chosen structured action unchanged from the recommendation layer
  - validates that the action is legal and currently resolvable
  - expands it into the exact `ExecutableLearningUnit`
  - starts a session without exposing `unit_id` choice to the UI
- update the frontend shell so the primary happy path is:
  - request next recommendation
  - show rationale
  - accept recommendation
  - enter session

## Bootstrap recommendation posture

The placeholder should behave like a deterministic bootstrap policy, not a full
learner-intelligence system.

Allowed bootstrap evidence:
- currently available launchable actions
- process-local reviewed session history for the same `user_id`
- latest evaluation summary for prior attempts on the same concept
- simple freshness/anti-loop checks

Disallowed shortcuts:
- raw UI heuristics in the client
- hidden `unit_id` recommendation as the public action contract
- direct learner-state mutation from recommendation

## Recommendation contract proposal

Recommended API:
- `POST /recommendations/next`

Minimal request shape:

```json
{
  "user_id": "demo-user"
}
```

Successful response shape:

```json
{
  "decision_id": "rec.0001",
  "policy_version": "bootstrap.recommendation.v1",
  "decision_mode": "rule_based",
  "candidate_actions": [
    {
      "mode": "Study",
      "session_intent": "LearnNew",
      "target_type": "concept",
      "target_id": "concept.alpha-topic",
      "difficulty_profile": "introductory",
      "strictness_profile": "supportive",
      "session_size": "single_unit",
      "delivery_profile": "text_first"
    }
  ],
  "chosen_action": {
    "mode": "Study",
    "session_intent": "LearnNew",
    "target_type": "concept",
    "target_id": "concept.alpha-topic",
    "difficulty_profile": "introductory",
    "strictness_profile": "supportive",
    "session_size": "single_unit",
    "delivery_profile": "text_first",
    "rationale": "Start with a supportive Study / LearnNew concept recall unit because there is no reviewed evidence for this concept yet."
  },
  "supporting_signals": [
    "no_prior_reviewed_attempt_for_target",
    "bootstrap_exploration_bias"
  ],
  "blocking_signals": [],
  "rationale": "Start with a supportive Study / LearnNew concept recall unit because there is no reviewed evidence for this concept yet.",
  "alternatives_summary": "Practice actions remain available but are downranked until there is reviewed evidence."
}
```

## Runtime acceptance contract proposal

Recommended API:
- `POST /runtime/sessions/start-from-recommendation`

Minimal request shape:

```json
{
  "user_id": "demo-user",
  "decision_id": "rec.0001",
  "action": {
    "mode": "Study",
    "session_intent": "LearnNew",
    "target_type": "concept",
    "target_id": "concept.alpha-topic",
    "difficulty_profile": "introductory",
    "strictness_profile": "supportive",
    "session_size": "single_unit",
    "delivery_profile": "text_first",
    "rationale": "Start with a supportive Study / LearnNew concept recall unit because there is no reviewed evidence for this concept yet."
  }
}
```

Runtime invariants:
- runtime validates the action rather than trusting the client blindly
- runtime resolves the action to an existing launchable unit
- runtime still owns session creation and event emission
- UI never sends a hand-built `unit_id`

## Placeholder ranking proposal

Use deterministic, concept-level heuristics over the current narrow action
space:

1. If there is no reviewed history for a concept, prefer `Study / LearnNew`
   over that concept.
2. If the latest reviewed attempt on a concept has a low score or missing
   dimensions, prefer `Practice / Remediate` for that same concept.
3. If the latest reviewed attempt is decent but still not strong, prefer
   `Practice / Reinforce`.
4. If reviewed performance is strong and there are unseen concepts left, prefer
   `Study / LearnNew` on the next unseen concept.
5. If all concepts are seen and no remediation is pressing, fall back to
   `Study / SpacedReview`.

Guardrails:
- never recommend `MockInterview`
- never recommend `Practice` for a concept with zero prior study/reviewed
  exposure unless the concept has no study action available
- avoid repeating the exact same `(mode, session_intent, target_id)` pattern
  more than twice in a row
- keep `session_size` fixed to `single_unit` in the placeholder

## Recommendation lifecycle events

Required in this slice:
- `recommendation_generated`
- `recommendation_shown`
- `recommendation_accepted`
- `recommendation_completed`

Scope note:
- `recommendation_skipped` can stay out of scope until the frontend exposes a
  real skip affordance
- for the thin frontend shell, `recommendation_shown` may be emitted when the
  recommendation response is returned to the interaction layer

## TDD plan

### Phase 1: recommendation engine tests

Add service-level tests first.

Recommendation engine contract:
- emits a versioned recommendation decision
- returns structured actions rather than raw unit IDs
- prefers bootstrap exploration when there is no reviewed history
- prefers remediation when reviewed evidence is weak
- preserves deterministic ordering and rationale
- rejects empty candidate space explicitly

### Phase 2: runtime action acceptance tests

Add runtime tests before API wiring.

Runtime contract:
- accepts a valid chosen recommendation action
- resolves the action to a launchable unit without exposing unit-choice logic to
  the client
- rejects unsupported or unresolvable actions fail-closed
- emits recommendation acceptance/completion events at the right boundaries

### Phase 3: API contract tests

Add API tests for recommendation generation and runtime start-from-action.

API contract:
- `POST /recommendations/next` returns the documented decision shape
- `POST /runtime/sessions/start-from-recommendation` returns the same session
  shape as manual start
- invalid action payloads or illegal combinations return explicit `4xx`
  errors
- health-only startup remains legal when content is not configured

### Phase 4: frontend flow tests

Update frontend tests after backend contracts exist.

Frontend contract:
- primary CTA requests a backend recommendation
- recommendation rationale is visible before start
- accepting the recommendation reaches the current prompt -> answer -> review
  loop
- manual launcher may remain as a bounded fallback/dev affordance

### Phase 5: bounded end-to-end verification

Verify locally and in CI:
- Python verification and smoke remain green
- frontend verification remains green
- browser-level flow from recommendation to review works against the local
  backend/frontend pair

## Test contract

- recommendation output is deterministic for the same process-local history
- recommendation response does not expose `unit_id` as the action contract
- action acceptance validates action legality and current resolvability
- generated recommendation events preserve decision/action traceability
- current manual flow remains available unless explicitly removed in a later
  slice
- no recommendation code is embedded in frontend heuristics

## Acceptance criteria

- repository contains a narrow `recommendation_engine` implementation
- a learner can request one next-step recommendation and start a session from it
- recommendation and runtime remain separate bounded contexts in code
- rationale and policy version are visible in the response/UI
- existing manual prototype loop still works after the new path lands
- implementation docs remain in sync

## Weak spots and assumption review

- weak spot: without learner projection, recommendation context will be
  intentionally shallow and process-local
- weak spot: if runtime action acceptance becomes too permissive, the client
  could smuggle illegal actions through a recommendation-shaped API
- weak spot: if recommendation starts ranking raw launchable units instead of
  structured actions, the placeholder will already be off-contract
- hidden assumption: the placeholder can treat the latest reviewed evaluation
  as enough signal for bounded remediation/reinforcement heuristics
- hidden assumption: recommendation-generated and recommendation-shown may be
  emitted back-to-back in the current thin UI
- no contradiction found with v2.2 baseline if the placeholder stays explicit
  about its bootstrap scope and does not masquerade as a full learner model

## ADR check

No ADR is required if this slice:
- keeps recommendation as a separate module family
- preserves the structured-action contract
- treats learner projection as deferred rather than silently redefined

## Definition of done

- explicit slice-level TDD contract exists and is reviewed
- recommendation replaces manual launch as the primary learner path
- runtime starts from structured recommendation actions, not client-built
  `unit_id`s
- browser-level recommendation -> review flow is verified
- implementation docs remain in sync
