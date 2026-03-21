# Slice 013c: Mock Outcome Projection Feedback

## Status

- completed

## Execution posture

`013c` is the narrow follow-up slice after `013a` and `013b`.

It exists only to close the remaining acceptance gap in `013`:
- reviewed and abandoned mock attempts must feed back into
  `learner_projection`
- later recommendation decisions must reflect those outcomes
- no new runtime, evaluator, or UI surface should be introduced

This slice must stay small enough to avoid reopening mock runtime design.

## Goal

Make post-mock feedback honest and stable without expanding the current bounded
mock path.

Expected outcome:
- reviewed mock attempts update subskills and trajectory state in a way that is
  distinguishable from concept-recall drills
- mock-only history no longer pollutes concept-level weak/review-due surfaces
- later recommendations do not immediately loop back into another mock after a
  recent mock attempt

## Why this slice exists

After `013b`, the repository already has a real
`MockInterview / ReadinessCheck` path.

Remaining gap against parent `013`:
- `learner_projection` still treats any reviewed unit as concept evidence keyed
  by `source_content_id`, which is wrong for scenario-backed mock units
- this can create false concept weakness on `scenario.url-shortener.basic`
- trajectory state remains too concept-centric when the learner only has mock
  evidence
- recommendation can still re-suggest mock too eagerly because recent mock
  outcome feedback is not yet policy-visible enough

## Affected bounded contexts

- `learner_projection`
- `recommendation_engine`
- narrow consumption in `learner_summary`

## Non-goals

- no new runtime states or events
- no evaluator redesign
- no scenario-to-concept mapping layer
- no per-scenario learner-state maps
- no UI changes unless an existing learner summary contract must be clarified
- no second scenario family

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- keep recommendation policy deterministic and rationale-bearing
- do not interpret scenario mock outcomes as ordinary concept-recall evidence
- do not add public API fields unless unavoidable
- respect `learner_state_update_rules_v1.md` anti-goal:
  no per-card-type or per-scenario learner maps in v1

## Hidden assumptions locked for this slice

- `URL Shortener` mock outcomes should not create concept-level
  weak/review-due entries until an explicit scenario-to-concept binding exists
- mock feedback should flow through:
  - `subskill_state`
  - `trajectory_state`
  - recommendation context assembly
- recommendation may consume recent mock outcome context from existing runtime
  read seams, but learner-state reasoning remains projection-owned

## Architectural approaches considered

### Option A: Projection-first feedback with bounded recommendation cooldown

- make `learner_projection` scenario-aware enough to avoid concept-state
  pollution
- let mock-reviewed and mock-abandoned attempts affect subskills and trajectory
- let recommendation consume that projection plus existing recent reviewed
  outcomes to suppress immediate re-mock loops

Trade-offs:
- preserves bounded-context ownership
- fixes the incorrect concept-state behavior directly
- keeps policy explainable and deterministic
- requires touching both projection and recommendation seams

### Option B: Recommendation-only direct mock memory

- leave projection mostly unchanged
- let recommendation inspect runtime history directly and patch over mock loops

Trade-offs:
- smaller diff at first glance
- leaves incorrect learner-state semantics in place
- pushes learner reasoning into the wrong bounded context
- rejected

Decision:
- choose Option A

## Proposed implementation shape

### 1. Projection should stop treating mock scenario ids as concept ids

Rules:
- `scenario_readiness_check` reviewed sessions must not populate `concept_state`
  under raw scenario ids
- mock-reviewed sessions should continue contributing to:
  - `subskill_state`
  - `trajectory_state`
- learner summary weak/review-due surfaces must therefore remain concept-owned
  and not surface scenario ids as concept targets

### 2. Mock evidence should affect trajectory state explicitly

Expected behavior:
- completed strong mock attempts can increase or stabilize
  `mock_readiness_estimate` and `mock_readiness_confidence`
- weak or fragile reviewed mock attempts can stall or lower readiness
- abandoned mock attempts should weigh meaningfully in
  `recent_abandonment_signal` and `recent_fatigue_signal`
- trajectory must not collapse to an all-zero posture when the learner has
  mock-only reviewed evidence

Rules:
- stay within existing conservative posture
- do not introduce per-scenario state maps
- prefer coarse, deterministic aggregates over new opaque heuristics

### 3. Recommendation should avoid immediate re-mock loops

Expected behavior:
- a recent reviewed mock attempt should suppress an immediate repeat
  `MockInterview / ReadinessCheck` recommendation
- a recent abandoned mock attempt should suppress re-mock more strongly
- recommendation should fall back to non-mock actions without changing the
  public API shape

Rules:
- the suppression should be deterministic and test-covered
- recommendation should still rely on learner projection for learner-state
  semantics
- direct runtime consumption is allowed only as bounded recommendation context,
  not as a replacement for projection logic

## TDD plan

Write tests first.

### Test file contract

- `backend/tests/test_learner_projection.py`
  Mock-only projection behavior, scenario-evidence handling, and trajectory
  feedback from reviewed or abandoned mock attempts.
- `backend/tests/test_recommendation_engine.py`
  Later recommendation behavior after recent mock review or abandonment.
- `backend/tests/test_learner_summary.py`
  Optional learner-facing summary guard that scenario ids do not leak into
  concept weak/review-due surfaces and readiness no longer looks empty after
  mock-only evidence.

### Phase 1. Projection correctness

Lock tests that prove:
- reviewed mock sessions do not create `concept_state["scenario.*"]`
- reviewed mock sessions still strengthen:
  - `tradeoff_reasoning`
  - `communication_clarity`
- mock-only reviewed history produces non-zero trajectory signals instead of an
  empty/unknown profile
- abandoned mock sessions raise trajectory abandonment/fatigue without creating
  false concept weakness

### Phase 2. Recommendation feedback

Lock tests that prove:
- after a recent reviewed mock attempt, the next recommendation is not an
  immediate mock repeat
- after a recent abandoned mock attempt, the next recommendation suppresses
  mock more strongly
- recommendation output shape remains unchanged

### Phase 3. Learner-summary guardrails

Lock tests that prove:
- learner summary does not surface raw scenario ids as concept weak/review-due
  entries after mock-only history
- readiness summary can still reflect non-zero mock trajectory evidence from
  mock-only history

## Acceptance criteria

- mock-reviewed outcomes no longer pollute concept-level learner state
- mock-reviewed and mock-abandoned attempts affect trajectory state
  meaningfully and deterministically
- later recommendation decisions reflect recent mock outcomes without changing
  API shape
- no new runtime/evaluator/UI surface is introduced
- the remaining acceptance gap in parent `013` is closed without adding
  per-scenario learner-state maps

## Weak spots and open questions

- without explicit scenario-to-concept binding, this slice must not pretend to
  know which concepts a scenario should update directly
- recommendation fallback after a suppressed mock may still choose generic
  non-mock work when concept evidence is sparse; that is acceptable for this
  slice
- if user-facing learner summary needs stronger mock-specific messaging, that
  should be a separate follow-up and not expand this slice

## Source-of-truth review

Checked against:
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`

Current assessment:
- no ADR should be required if `013c` stays within these bounds
- source-of-truth updates may be unnecessary if the slice remains an
  implementation of existing rules rather than a contract expansion

## Exit condition

`013c` is complete when the bounded mock path from `013b` feeds back into
learner projection and later recommendations honestly enough that parent `013`
can be closed without qualification.
