# Slice 006c: Practice Prompt Expansion

## Status

- completed in current worktree

## Goal

Make the current `Practice` launchable units materially more applied and visibly
different from `Study` without changing the bounded prototype seam:
- keep `unit_family = concept_recall`
- keep `binding.concept_recall.v1`
- keep the current single-response runtime loop

This slice should improve the usefulness of the current backend loop for real
technical content, but it must not pretend that scenario-family practice or a
multi-step player already exist.

## Why this is on the critical path

The current manual launcher and frontend shell are now demoable, but they
surface a product problem clearly:
- `Study` and `Practice` often look nearly identical to the learner
- the current prompt reads like a dry recall ticket
- adding recommendation on top of that would mostly automate a weak unit shape

Before building `recommendation_engine`, the backend should first produce a more
meaningful `Practice` unit within the already implemented `concept_recall`
prototype seam.

## In scope

- richer `visible_prompt` generation for `Practice` mode over the existing
  `concept_recall` unit family
- deterministic prompt assembly from already loaded concept metadata
- fallback behavior when optional content fields are empty or missing
- regression coverage that proves `Study` and `Practice` now diverge visibly
- preservation of the current runtime, API, and evaluator contracts

## Out of scope

- new unit families
- scenario-family materialization
- new evaluation bindings
- `MockInterview` support
- multi-unit session planning
- hint/reveal runtime expansion
- recommendation logic
- frontend redesign beyond consuming the unchanged `visible_prompt`

## Affected bounded contexts

- `learning_design`
- narrow `session_runtime` read surface regression coverage
- narrow `web_api / ui` compatibility through unchanged launch-option payloads

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/02_domain/learning_design_boundary.md`
- `docs/03_architecture/concept_recall_binding_v1.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/04_content/content_schema.md`
- `implementation/roadmap.md`
- `implementation/status.md`

## Constraints

- `Study` and `Practice` must remain within the existing `concept_recall`
  prototype seam
- `Practice` prompt enrichment must not require scenario objects, hint ladders,
  or new canonical axes because imported bundles do not provide them yet
- `evaluation_binding_id` must remain `binding.concept_recall.v1`
- runtime and API payload shapes should remain unchanged
- prompt generation must be deterministic and must not mutate loaded catalog
- prompt framing must stay within the current evaluation dimensions:
  what the concept is, when to use it, and the main trade-offs

## Hidden assumptions

- imported draft bundles may contain sparse or low-confidence fields such as
  `why_it_matters`, `when_to_use`, and `tradeoffs`; the implementation must
  treat them as optional input, not as required truth
- richer `Practice` wording is still useful even if the underlying evaluator
  remains rule-first and recall-oriented, provided the prompt does not demand
  unsupported output types
- some topics may still remain only modestly better if the available content is
  thin; this slice improves the current shape but does not solve content
  completeness

## Architectural approaches considered

### Option A: Mode-aware prompt enrichment inside the existing `concept_recall` family

- keep the current unit ids, binding, and runtime loop
- leave `Study` prompts in the current short recall form
- generate a richer `Practice` prompt from available concept fields such as
  `description`, `why_it_matters`, `when_to_use`, and `tradeoffs`
- keep the task anchored to the same three primary dimensions already scored by
  `binding.concept_recall.v1`

Trade-offs:
- smallest contract-preserving change
- directly addresses the current “Practice feels identical to Study” problem
- keeps evaluation and runtime seams stable
- improvement ceiling is limited by sparse content and the current evaluator

Decision:
- choose Option A

### Option B: Introduce a new applied unit family and binding

- create something like `applied_concept` or `mini_scenario_recall`
- give it richer prompts and a new evaluation contract

Trade-offs:
- would produce a more honest applied-practice shape
- immediately widens scope into learning-design and evaluation contracts
- would require new binding docs and likely broader source-of-truth updates

Rejected because:
- it is too large for the next bounded slice and would delay progress on the
  current prototype path

### Option C: Jump directly to scenario-family practice units

- materialize real `Scenario`-based units and align them to
  `scenario_rubric_binding_v1.md`

Trade-offs:
- best long-term product direction
- impossible to do honestly right now because imported content has no scenario
  drafts, no canonical axes, and no hint ladders

Rejected because:
- it would force the implementation to invent content and runtime semantics that
  the repository does not yet contain

## Proposed implementation shape

- extend `ExecutableLearningUnit` materialization with mode-aware prompt
  builders:
  - `Study`: keep the existing short recall prompt
  - `Practice`: build a richer prompt from available concept metadata
- the `Practice` prompt should:
  - open with a more applied framing, not just “Explain the concept”
  - optionally include `description`
  - optionally include one or more `why_it_matters` items
  - optionally mention `when_to_use` and `tradeoffs` when those lists are
    populated
  - always end with the same required response dimensions:
    what it is, when to use it, and the main trade-offs
- empty or missing optional fields should be omitted cleanly rather than
  rendered as empty sections
- keep `unit_id`, `source_content_ids`, `effective_difficulty`,
  `completion_rules`, and `evaluation_binding_id` unchanged

## TDD plan

### Phase 1: materializer contract tests first

Add or update materializer tests before implementation.

Materializer contract:
- `Study` prompt remains the current short recall prompt
- `Practice` prompt becomes visibly different for the same concept
- `Practice` prompt includes richer context when optional concept metadata is
  present
- `Practice` prompt falls back deterministically when optional fields are empty
- materialization remains deterministic and non-mutating
- current ids, bindings, and policy metadata are preserved

### Phase 2: runtime read-surface regression tests

Add or update runtime tests to prove the launcher path exposes the richer
`Practice` prompt without API changes.

Runtime contract:
- `list_manual_launch_options()` returns the same payload shape as today
- `Practice` launch options now carry the enriched `visible_prompt`
- `Study` launch options keep the existing prompt shape
- unsupported mode/intent pairs still fail closed

### Phase 3: runtime/evaluation compatibility regression

Add or update one runtime test that proves the existing submit/evaluate path
still works over a `Practice` unit after prompt enrichment.

Compatibility contract:
- `Practice` still produces `unit_family = concept_recall`
- evaluation still uses `binding.concept_recall.v1`
- no runtime state transition changes are introduced

## Test contract

- same concept can materialize into visibly different `Study` and `Practice`
  prompts
- prompt assembly ignores empty optional fields cleanly
- prompt assembly uses deterministic field ordering
- launch-option payload shape remains unchanged
- existing runtime/evaluation tests remain green
- no new unsupported mode/intent pair is introduced

## Acceptance criteria

- `Practice` is meaningfully more applied than `Study` in the current launcher
- backend API shapes do not change
- runtime still emits the same semantic events on the current prototype loop
- evaluator contract remains `binding.concept_recall.v1`
- current local verification remains green after the change

## Weak spots and assumption review

- weak spot: if `Practice` phrasing becomes too scenario-like, the current
  evaluator will under-specify what “good” means; the implementation must stay
  inside the three current concept-recall dimensions
- weak spot: imported content often has empty `when_to_use` and `tradeoffs`;
  tests must cover sparse-field fallback explicitly
- hidden assumption: using draft-exported explanatory text in a dev/demo prompt
  is acceptable when `allow_draft_bundles=True`; this slice must not silently
  turn draft text into a production truth claim
- hidden assumption: user-facing value comes primarily from prompt framing, not
  from new runtime mechanics; this is intentionally a bounded improvement
- no contradiction found with the v2.2 baseline as long as the implementation
  remains within `Learning Design` prompt framing and does not revise evaluator
  or runtime ownership

## ADR check

No ADR is required if this slice:
- preserves bounded-context ownership
- keeps `concept_recall` as the implemented unit family
- does not revise evaluation or recommendation contracts

## Definition of done

- explicit TDD plan exists and is reviewed
- roadmap and status reflect the new execution order
- materializer tests prove richer `Practice` prompt generation
- runtime tests prove unchanged payload shape with improved `Practice` prompt
- current verification remains green

## Outcome

- `Practice` prompt materialization is now visibly richer than `Study` while
  staying inside the existing `concept_recall` family
- `Study` prompt shape remains unchanged
- `Practice` prompt now uses available concept metadata such as `description`
  and `why_it_matters`, with deterministic fallback when optional fields are
  empty
- `evaluation_binding_id`, `unit_id`, runtime state transitions, and API payload
  shapes remain unchanged
- regression coverage now proves `Practice` prompt differentiation at the
  materializer, runtime service, and API layers
