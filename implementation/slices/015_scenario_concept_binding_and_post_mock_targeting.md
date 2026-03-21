# Slice 015: Scenario-to-Concept Binding and Post-Mock Targeting

## Status

- completed

## Execution posture

`015` follows the completed `013` wave.

Purpose:
- turn the first bounded mock path into a better curriculum node rather than an
  isolated branch
- let weak or partial mock outcomes drive meaningful next-step targeting
- keep the change bounded to one scenario family before validating breadth

Binding model is chosen for implementation:
- use explicit scenario field `bound_concept_ids`
- seed a minimal topic-scoped `url-shortener` concept pack first
- preserve the existing scenario-facing `url-shortener` catalog title

## Goal

Introduce an explicit, auditable bridge from scenario-backed mock outcomes to
canonical concept-level follow-up targeting.

Expected outcome:
- `URL Shortener` mock outcomes can update relevant concept evidence
  conservatively instead of disappearing into trajectory-only state
- later recommendations can propose concept-level recovery or reinforcement
  tied to the mock domain
- the system no longer has to choose between:
  - raw scenario-id pollution in learner state, or
  - zero concept-level feedback after mock work

## Why this slice exists

After `013a`/`013b`/`013c`, the repository has:
- one real `MockInterview / ReadinessCheck` path
- mock outcome feedback into `trajectory_state` and `subskill_state`
- bounded suppression of immediate re-mock loops

What is still missing:
- concept-level feedback from scenario work
- concept-level post-mock targeting

Current repository reality:
- test fixtures contain only three topic bundles:
  - `alpha-topic`
  - `zeta-topic`
  - `url-shortener`
- `url-shortener` currently has `scenarios[]` but no canonical `concepts[]`
- there are therefore no canonical concept ids for `URL Shortener` that a
  post-mock recommendation could target honestly

Implication:
- `015` cannot be only about a binding table
- it must also seed a minimal canonical concept pack for `url-shortener`, or
  else recommendation still has nowhere concrete to land after a mock

## Affected bounded contexts

- `content_kernel`
- `learning_design`
- `learner_projection`
- `recommendation_engine`
- narrow consumption in `learner_summary`

## Non-goals

- no second scenario family in the same slice
- no new mock runtime behavior
- no new evaluation mode
- no full scenario graph or concept-graph framework
- no open-ended curriculum planner
- no per-scenario learner-state maps
- no attempt to solve generic many-to-many binding for all future families in
  one pass

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- recommendation still selects structured learning actions, not curricula
- learner-state updates remain deterministic and conservative
- `learner_projection` owns learner-state semantics
- `recommendation_engine` owns ranking and guardrails
- scenario-backed work must not update arbitrary concepts without an explicit
  binding
- parent `013` should remain the first closed mock wave, not be reopened

## Hidden assumptions to lock before code

- the first bound family remains `URL Shortener`
- the first post-mock targets should be a small concept subset, not the full
  v1 content pack
- concept-level updates from scenario evidence should be moderate and
  conservative, not equivalent to direct concept-recall evidence
- strong follow-up handling should still weigh more heavily on subskills than on
  raw concepts

## Binding-model options

### Option A: Static binding registry in code plus concept seeding

Shape:
- seed minimal `url-shortener` canonical concepts in content fixtures
- add a materializer- or content-kernel-owned static mapping:
  - `scenario.url-shortener.basic -> [concept ids...]`
- carry `bound_concept_ids` into runtime unit metadata
- let `learner_projection` use that metadata when interpreting reviewed mock
  outcomes

Pros:
- smaller implementation diff
- no content schema revision
- easiest first pass if we only need one family fast

Cons:
- binding becomes a hidden repository contract
- authoring and implementation can drift
- less scalable once a second or third family is added
- weaker alignment with “repository as source of truth” posture

### Option B: Content-first explicit scenario binding support

Shape:
- seed minimal `url-shortener` canonical concepts in content fixtures
- extend the content/source-of-truth model with one explicit optional scenario
  support field, for example:
  - `related_concepts`
  - `bound_concept_ids`
- load and validate that field from content
- materialize it into runtime unit metadata for projector/recommendation use

Pros:
- binding is explicit, reviewable, and authorable
- better long-term fit for additional scenario families
- avoids hardcoded hidden coupling in implementation code
- stronger match for the repo’s knowledge-base posture

Cons:
- broader change surface
- requires schema/example/documentation updates
- slightly more up-front work before the first concept-targeting payoff

## Recommendation

Choose Option B.

Reasoning:
- `015` is introducing a load-bearing knowledge relationship, not a temporary
  runtime quirk
- the repository currently has no canonical `URL Shortener` concept pack, so
  the slice already needs content work
- once content must move anyway, hiding the binding in code becomes the weaker
  engineering choice

Fallback posture if scope must stay tighter:
- Option A is acceptable only if explicitly marked as a temporary bridge and
  bounded to `URL Shortener`

## Proposed implementation shape

### 1. Seed minimal `URL Shortener` concept pack

Add a small canonical concept set to the `url-shortener` topic bundle.

Recommended first set:
- `concept.url-shortener.id-generation`
- `concept.url-shortener.storage-choice`
- `concept.url-shortener.read-scaling`
- `concept.url-shortener.caching`

Rules:
- keep the set intentionally small
- each concept must be usable by existing `Study`/`Practice`
  concept-recall materialization
- the topic should become eligible for both:
  - `mini_scenario`
  - `recall`

### 2. Add explicit scenario-to-concept binding metadata

Recommended first shape:
- one optional scenario field carrying canonical concept ids

Rules:
- the binding must point only to canonical concept ids that exist in the same
  repository state
- the binding must stay deterministic and schema-valid
- the first slice only needs one scenario record and one family

### 3. Materialize binding into runtime-readable unit metadata

Expected unit metadata addition:
- `bound_concept_ids`

Rules:
- projector must not infer concept ids from `expected_focus_areas`
- runtime must remain a passive carrier, not the owner of learner-state logic
- existing concept-recall unit families must remain stable

### 4. Update learner projection conservatively

Expected behavior:
- reviewed mock outcomes may update bound concepts conservatively
- strong mock performance should not equal direct concept mastery
- weak mock performance can create or reinforce fragility on bound concepts
- abandoned mock sessions still remain trajectory-only unless there is reviewed
  evidence

Recommended projection posture:
- scenario evidence contributes lower concept weight than direct
  concept-recall evidence
- scenario evidence can update:
  - `proficiency_estimate`
  - `confidence`
  - `review_due_risk`
  - `hint_dependency_signal`
- subskill and trajectory behavior from `013c` stays intact

### 5. Recommendation should use the new concept feedback

Expected behavior:
- after a weak `URL Shortener` mock, recommendation can steer into the bound
  concepts rather than generic fallback behavior
- after a strong mock, recommendation may still prefer conservative
  reinforcement/review rather than another mock
- public API shape must remain unchanged

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_content_api.py`
  Topic summary/detail projection for the expanded `url-shortener` bundle.
- `backend/tests/test_executable_learning_unit_materializer.py`
  Materialized mock unit carries `bound_concept_ids`; concept-recall units exist
  for the seeded `url-shortener` concepts.
- `backend/tests/test_learner_projection.py`
  Scenario evidence updates bound concepts conservatively rather than raw
  scenario ids.
- `backend/tests/test_recommendation_engine.py`
  Weak mock outcomes can drive concept-level follow-up targeting on bound
  concepts.
- `backend/tests/test_learner_summary.py`
  Learner-facing weak/review_due surfaces can now show canonical
  `url-shortener` concepts after mock outcomes, never raw scenario ids.

### Phase 1. Content and materialization readiness

Lock tests that prove:
- `url-shortener` now exposes canonical concepts and one scenario
- `url-shortener` topic summary still surfaces `Design a URL Shortener` as the
  display title after concept seeding
- the scenario record carries explicit bound concept ids
- `Study`/`Practice` materialization now produces concept-recall units for the
  seeded `url-shortener` concepts
- `MockInterview / ReadinessCheck` materialization carries those
  `bound_concept_ids`

### Phase 2. Projection semantics

Lock tests that prove:
- reviewed weak mock outcomes update the bound concepts, not `scenario.*`
- concept updates remain weaker than direct concept-recall evidence
- strong mock outcomes do not immediately create false “mastered” concepts
- abandoned mock sessions do not create concept weakness without reviewed
  evidence

### Phase 3. Recommendation targeting

Lock tests that prove:
- after a weak `URL Shortener` mock, recommendation selects a bound concept
  recovery/reinforcement action instead of another mock
- recommendation rationale explains the post-mock targeting
- strong mock outcomes still avoid immediate re-mock loops

### Phase 4. Summary guardrails

Lock tests that prove:
- learner summary surfaces canonical concept titles from the new binding
- raw scenario ids never appear in weak/review_due learner-facing payloads

## Acceptance criteria

- `url-shortener` has a minimal canonical concept pack suitable for
  concept-recall targeting
- one explicit scenario-to-concept binding exists and is materialized into
  runtime-readable metadata
- learner projection uses that binding conservatively for reviewed mock outcomes
- recommendation can target bound concepts after weak mock outcomes
- no raw scenario ids leak into concept-level learner surfaces

## Weak spots and open questions

- adding content-schema support for scenario bindings likely requires
  source-of-truth updates, not just implementation
- seeding canonical concepts into `url-shortener` would currently flip the
  topic catalog display title to the first concept title unless the summary
  projection keeps scenario-led bundles scenario-facing
- if the first concept pack is too small, recommendation may overfit a narrow
  subset of `URL Shortener`
- if concept weights are too strong, scenario evidence will over-claim mastery;
  if too weak, the slice will not materially improve targeting
- if we choose Option A instead, that temporary nature must be documented
  explicitly

## Source-of-truth review

This slice likely touches or depends on:
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`

Current assessment:
- ADR probably still not required if this remains a bounded clarification of
  content-to-learning-design linkage
- source-of-truth and example-content updates are likely required under
  Option B

## Exit condition

`015` is complete when a weak `URL Shortener` mock attempt can lead to honest
concept-level post-mock targeting through explicit bindings, without
reintroducing raw scenario-id pollution or hidden code-only coupling.
