# Slice 013a: URL Shortener Scenario Seed

## Status

- planned

## Goal

Remove the current executable-content blocker for `013` by introducing one
bounded scenario-backed learning unit path that can honestly support a future
`MockInterview / ReadinessCheck` vertical slice.

This slice does not implement mock runtime, evaluation, or UI. It only makes
the first scenario-family path materializable and testable without violating the
current binding docs.

## Why this slice exists

Current repository posture after `011` and `012`:
- `concept_recall` remains the only executable unit family
- `concept_recall_binding_v1.md` explicitly rejects `MockInterview`
- draft content fixtures expose `scenarios: []`
- recommendation/runtime/evaluation therefore have no legal scenario-backed
  mock path to consume

Without this slice, any attempt to implement `013` would either:
- fake a mock interview on top of `concept_recall`, or
- broaden scope into a multi-family redesign without a bounded first target

## Affected bounded contexts

- `learning_design`
- `content_kernel`
- narrow consumption in `session_runtime`
- narrow consumption in `recommendation_engine`

## Non-goals

- no runtime follow-up implementation yet
- no new evaluator logic yet
- no learner-facing mock UI yet
- no recommendation unlock behavior yet
- no broad scenario-authoring framework
- no second scenario family in the same slice
- no change to `concept_recall` behavior

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- do not expand `concept_recall` into pseudo-mock behavior
- the first scenario path must use an existing scenario binding from
  `scenario_rubric_binding_v1.md`
- the seeded unit family must be narrow, deterministic, and bounded to one
  follow-up envelope
- existing `Study` and `Practice` materialization must remain unchanged
- if source-of-truth docs need revision, stop and update them explicitly rather
  than silently drifting from current contracts

## Chosen first scenario family

- `URL Shortener`

Rationale:
- it already has an explicit scenario binding in
  `scenario_rubric_binding_v1.md`
- its expected axes and gating conditions are concrete and bounded
- it is a cleaner first deterministic evaluator target than broader families
  like `Chat System`
- it supports a credible single follow-up round without requiring an
  open-ended interviewer loop

## Architectural approaches considered

### Option A: Add one new bounded scenario-backed unit family

- introduce a new executable learning unit family for
  `MockInterview / ReadinessCheck`
- seed it from canonical `scenarios[]` content
- keep the family restricted to one scenario family in the first pass

Trade-offs:
- smallest honest unblocker for `013`
- keeps `concept_recall` untouched
- cleanly aligns content, learning design, and later evaluator/runtime work
- requires one new unit-family seam instead of reusing current materializer path

### Option B: Broaden concept-recall materialization to support MockInterview

- reuse existing `concept_recall` family and simply allow `MockInterview`

Trade-offs:
- smaller short-term diff
- directly conflicts with `concept_recall_binding_v1.md`
- produces a dishonest mock path
- rejected

### Option C: Seed multiple scenario families at once

- add `URL Shortener`, `Rate Limiter`, and others in one pass

Trade-offs:
- better eventual breadth
- slower and riskier first unblocker
- mixes content-seeding scope with later policy/runtime/evaluator scope
- rejected

Decision:
- choose Option A

## Proposed implementation shape

### 1. Add one bounded topic fixture with scenario content

Introduce one new draft bundle dedicated to the first scenario-backed path.

Recommended bundle posture:
- topic slug: `url-shortener`
- one canonical scenario:
  - `id = scenario.url-shortener.basic`
  - `title`
  - `prompt`
  - `content_difficulty_baseline`
  - `expected_focus_areas`
  - `canonical_axes`
  - `canonical_follow_up_candidates`
- optional `hidden_constraints` only if needed to make the first follow-up
  deterministic
- `learning_design_drafts.candidate_card_types` should contain the exact marker
  `mini_scenario`

Rules:
- do not overload existing `alpha-topic` / `zeta-topic` concept fixtures with
  pseudo-scenarios
- keep the seeded scenario minimal but schema-valid
- keep the first bundle auditable and easy to reason about in tests
- in this slice, `mini_scenario` is only a content-side eligibility marker; it
  does not itself imply runtime behavior or recommendation unlock

### 2. Introduce a new executable unit family

Add a new bounded materialization family rather than stretching
`concept_recall`.

Recommended first family id:
- `scenario_readiness_check`

Expected unit posture:
- `mode = MockInterview`
- `session_intent = ReadinessCheck`
- `target_type = scenario_family` or equivalent unit metadata that preserves
  the scenario-family identity
- `follow_up_envelope.max_follow_ups = 1`
- `follow_up_envelope.follow_up_style = bounded_probe`
- stricter hint policy than `Practice`
- `completion_rules.allows_answer_reveal = false`

Rules:
- `supported_materialization_pairs()` should grow by exactly one new pair:
  `("MockInterview", "ReadinessCheck")`
- materialization should include only seeded scenario-backed units for this
  slice
- existing concept-recall pairs must remain stable
- this slice only requires the new unit metadata to encode the stricter
  follow-up and support policy; runtime enforcement is deferred to `013b`

### 3. Preserve explicit binding metadata

The materialized unit must carry enough metadata for later runtime/evaluation
dispatch.

Required metadata additions or guarantees:
- `unit_family = scenario_readiness_check`
- `scenario_family = url_shortener`
- `evaluation_binding_id = binding.url_shortener.v1`
- `source_content_ids` should point to the seeded scenario id

Rules:
- `scenario_family` and `evaluation_binding_id` should come from one explicit
  materializer-owned static mapping keyed by canonical scenario id
- this slice should not invent dynamic binding lookup in runtime
- the unit metadata should make later evaluator dispatch straightforward
- do not add `scenario_family` as a new canonical content field in this slice

## Input contract for this slice

The slice may assume:
- content bundles continue loading through `load_topic_catalog(...)`
- topic detail APIs continue projecting canonical `scenarios[]`
- materialization remains deterministic and in-process

The slice must not assume:
- any preexisting scenario fixtures in the repo
- multi-turn runtime support already exists
- a scenario evaluator already exists

## TDD plan

Write tests first.

### Test layer 1: content fixture and catalog loading

1. a new `url-shortener` draft bundle loads successfully through the existing
   catalog reader
2. topic summary/detail surfaces expose `scenario_count = 1` for that bundle
3. the scenario payload survives projection with required canonical fields

### Test layer 2: materialization contract

1. `supported_materialization_pairs()` now includes exactly one new pair:
   `("MockInterview", "ReadinessCheck")`
2. materializing `MockInterview / ReadinessCheck` returns exactly one seeded
   unit for the new fixture
3. the new unit is deterministic and stable across repeated runs
4. the new unit carries:
   - `unit_family = scenario_readiness_check`
   - `scenario_family = url_shortener`
   - `evaluation_binding_id = binding.url_shortener.v1`
   - `follow_up_envelope.max_follow_ups = 1`
   - `completion_rules.allows_answer_reveal = false`
5. `Study` and `Practice` concept-recall materialization remains byte-for-byte
   unchanged for existing fixtures
6. the current manual launcher surface does not gain new options from this
   slice alone

### Test layer 3: negative contract tests

1. the new mock materialization path skips topics without scenarios
2. the new mock materialization path skips topics that have scenarios but do
   not advertise `mini_scenario` eligibility
3. malformed scenario records still fail loudly and deterministically
4. `concept_recall` still rejects unsupported `MockInterview` requests when
   routed through the old path

## Acceptance criteria

- the repository contains one schema-valid scenario-backed fixture for
  `URL Shortener`
- the materializer can legally produce one bounded
  `MockInterview / ReadinessCheck` executable unit
- the produced unit contains enough metadata to support later runtime and
  evaluator dispatch
- existing `Study` and `Practice` flows remain unchanged
- the current manual launcher and session UI do not gain mock behavior in this
  slice
- no runtime, evaluator, or frontend behavior is broadened in this slice

## Weak spots and hidden assumptions

- `mini_scenario` is now fixed as the first eligibility marker for this slice,
  but the repository does not yet define a broader enumerated vocabulary for
  all future scenario-derived card types
- `scenario_family` naming must align with
  `scenario_rubric_binding_v1.md`; this slice resolves the current ambiguity by
  using an explicit materializer-owned mapping keyed by canonical scenario id
- this slice assumes one follow-up candidate is enough for the first bounded
  readiness check; if runtime later needs richer sequencing, that belongs to
  `013b`, not here

## Source-of-truth review

Reviewed against:
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `docs/03_architecture/concept_recall_binding_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`

Current conclusion:
- this slice is consistent with source-of-truth as long as it introduces a new
  scenario-backed family instead of extending `concept_recall`

## Exit condition to start 013b

`013a` is complete when:
- the new fixture and materialization tests are green
- the new unit family exists and is stable
- there is a legal scenario-backed executable unit for
  `MockInterview / ReadinessCheck`

Only after that should `013b` start runtime follow-up implementation.
