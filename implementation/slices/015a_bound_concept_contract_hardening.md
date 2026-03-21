# Slice 015a: Bound Concept Contract Hardening

## Status

- completed

## Execution posture

`015a` is a corrective follow-up to completed `015`.

Purpose:
- make the current branch push-safe without pretending the repository already
  has honest concept-specific mock feedback
- remove the current false precision in post-mock concept targeting
- align content, runtime, and authoring contracts around `bound_concept_ids`

This slice is intentionally narrower than `015`.
It is a hardening and rollback pass, not the final semantic solution.

## Goal

Remove the current load-bearing risks around `bound_concept_ids` and restore a
conservative learner-state posture until richer concept-specific mock evidence
exists.

Expected outcome:
- no dangling `bound_concept_ids` can silently enter runtime
- reviewed mock sessions no longer create false concept-specific learner state
- recommendation no longer claims concept-level post-mock remediation from
  coarse scenario evidence
- the repository keeps the explicit binding field, but stops over-claiming what
  it means

## Why this slice exists

Review of `origin/main..HEAD` found five concrete issues:
- `bound_concept_ids` has no referential-integrity enforcement
- mock evidence is smeared identically across all bound concepts
- recency remains anchored to the latest session event instead of review time
- importer/runtime/docs are misaligned on the new binding contract
- recommendation-start recovery still has an idempotency gap on stale `409`

`015a` addresses only the first, second, and fourth items directly.
The recency fix and stale-retry hardening remain separate follow-ups because
they are orthogonal and should not be mixed into this rollback pass.

## Affected bounded contexts

- `content_kernel`
- `learning_design`
- `learner_projection`
- `recommendation_engine`
- importer/validation tooling under content authoring support

## Non-goals

- no new evaluator contract
- no per-concept scenario scoring in this slice
- no new runtime behavior for mock sessions
- no frontend or API redesign
- no second scenario family
- no attempt to complete the deferred `016` semantics here

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- keep recommendation selecting bounded structured actions
- keep learner-state updates deterministic and conservative
- do not make `bound_concept_ids` a hidden runtime-only convention
- do not broaden recommendation to generic curriculum planning
- do not let mock evidence claim concept precision it does not actually have

## Hidden assumptions to lock before code

- `URL Shortener` remains the only scenario family involved in this pass
- `bound_concept_ids` should remain in content as explicit metadata, but should
  not drive concept-state updates until richer semantics exist
- importer heuristics should not invent load-bearing bindings automatically
- the repository should prefer a truthful conservative rollback over keeping a
  misleading product-visible behavior

## Corrective options

### Option A: Push-safe rollback and contract hardening

Shape:
- keep `bound_concept_ids` as explicit optional content metadata
- validate referential integrity when the field is present
- stop using the field to update `concept_state`
- stop using the field to drive concept-level post-mock recommendation
- clarify that importer heuristics do not derive this field automatically

Pros:
- smallest safe corrective diff
- removes false concept precision immediately
- keeps the repo honest about current evidence quality
- avoids forcing importer heuristics to invent semantic bindings

Cons:
- partially retracts the visible `015` concept-targeting behavior
- leaves `bound_concept_ids` mostly preparatory until `016`

### Option B: Complete the semantic fix now

Shape:
- add richer mapping from scenario criteria to bound concepts
- let evaluator or projection emit concept-specific mock signals
- keep concept-level post-mock targeting enabled

Pros:
- preserves the intended `015` product direction
- avoids a temporary rollback in user-facing behavior

Cons:
- materially larger scope
- risks mixing content contract, evaluator semantics, and recommendation policy
- no longer a hardening slice

## Recommendation

Choose Option A.

Reasoning:
- current concept-level mock feedback is semantically wrong, not merely
  under-tuned
- a conservative rollback is lower risk than shipping false concept-level
  targeting
- the richer solution belongs in a separate `016` slice with a new test
  contract, not in a corrective pass

## Proposed implementation shape

### 1. Harden `bound_concept_ids` as passive validated metadata

Behavior:
- if `bound_concept_ids` is present, every id must resolve to a real concept in
  the materialized repository state
- malformed or dangling ids fail closed
- missing `bound_concept_ids` must not crash unrelated runtime paths

Rules:
- validation should happen before learner projection or recommendation can
  observe the ids
- the field remains optional at the global schema level
- the field should be treated as author-curated, not heuristic-by-default

### 2. Roll back mock-to-concept learner updates

Behavior:
- reviewed mock sessions continue to update `subskill_state` and
  `trajectory_state`
- reviewed mock sessions stop writing concept-level evidence derived only from
  coarse blended scenario scoring
- no raw `scenario.*` ids leak into `concept_state`

Rules:
- rollback should preserve the `013c` feedback loop on trajectory/subskills
- this slice must not introduce fake per-concept weighting heuristics

### 3. Remove concept-level post-mock remediation derived from coarse binding

Behavior:
- recommendation continues to suppress immediate re-mock loops
- recommendation stops selecting bound concepts purely because a recent mock
  listed them in `bound_concept_ids`
- automatic post-mock concept targeting is deferred until `016`

Rules:
- rationale should remain truthful about the current confidence level
- no public API shape changes are required in this slice

### 4. Align authoring and validation posture

Behavior:
- docs clearly state that `bound_concept_ids` is explicit author-managed
  metadata
- validator understands and checks the field when present
- importer mapper is not required to infer the field heuristically in this pass

Rules:
- do not silently claim authoring support that the importer does not yet
  provide
- if importer output cannot derive the field, that limitation must be explicit

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_executable_learning_unit_materializer.py`
  `bound_concept_ids` fails closed when it references unknown concept ids; mock
  materialization does not depend on coarse concept-targeting semantics.
- `backend/tests/test_learner_projection.py`
  reviewed mock sessions stay out of `concept_state` until richer evidence
  exists; subskill and trajectory signals remain intact.
- `backend/tests/test_recommendation_engine.py`
  recent mock attempts suppress immediate re-mock loops, but do not trigger
  concept-specific remediation solely from `bound_concept_ids`.
- `backend/tests/test_learner_summary.py`
  learner-facing summary never leaks dangling or raw scenario ids after the
  rollback.
- `tools/system-design-space-importer/tests/test_validator.py`
  validator rejects unknown `bound_concept_ids` when the field is present and
  tolerates its absence when no richer contract is claimed.

### Phase 1. Binding integrity

Lock tests that prove:
- a scenario with `bound_concept_ids: ["concept.missing"]` fails closed
- valid `bound_concept_ids` continue to materialize as passive metadata
- absence of `bound_concept_ids` does not crash generic content loading

### Phase 2. Projection rollback

Lock tests that prove:
- reviewed mock sessions do not create `concept_state` from blended scenario
  scores
- mock feedback still updates `tradeoff_reasoning`,
  `communication_clarity`, and `mock_readiness_*`
- abandoned mock sessions remain trajectory-only

### Phase 3. Recommendation rollback

Lock tests that prove:
- weak post-mock learner state does not automatically target a bound concept
  just because the scenario listed one
- immediate re-mock suppression still works
- recommendation remains deterministic after the rollback

### Phase 4. Validation posture

Lock tests that prove:
- validator understands `bound_concept_ids` when present
- validator rejects unresolved ids
- validator does not require the field globally for every scenario draft

## Acceptance criteria

- no dangling `bound_concept_ids` can reach runtime
- reviewed mock sessions no longer claim concept-specific evidence from coarse
  blended scoring
- recommendation no longer advertises concept-level post-mock remediation based
  only on `bound_concept_ids`
- docs and validator agree that `bound_concept_ids` is explicit
  author-managed metadata, not heuristic importer output
- branch becomes safe to push without misleading concept-level semantics

## Weak spots and open questions

- if we keep `bound_concept_ids` optional globally, the validator must be clear
  about what it validates versus what it merely permits
- this slice intentionally leaves `bound_concept_ids` underused until `016`;
  that temporary state should be called out explicitly to avoid future
  confusion
- if product requires concept-level post-mock remediation immediately, `015a`
  is the wrong corrective slice and we should stop and design `016` first

## Source-of-truth review

This slice likely touches or depends on:
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`

Current assessment:
- ADR likely not required because this slice narrows behavior back toward the
  conservative baseline rather than introducing a new architectural direction
- local source-of-truth updates are likely required to clarify the authoring and
  validation posture of `bound_concept_ids`
- no contract docs currently require coarse concept-level mock feedback, so the
  rollback does not appear to conflict with the frozen baseline

## Exit condition

`015a` is complete when the repository no longer ships false concept-level
post-mock semantics, and `bound_concept_ids` is either valid explicit metadata
or rejected before runtime can depend on it.
