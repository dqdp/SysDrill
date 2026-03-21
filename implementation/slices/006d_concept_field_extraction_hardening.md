# Slice 006d: Concept Field Extraction Hardening

## Status

- completed in current worktree

## Goal

Improve importer-side semantic extraction for concept-level fields that are
already part of the current content schema:
- `when_to_use`
- `tradeoffs`
- `why_it_matters`

This slice should increase the pedagogical usefulness of imported topic bundles
without changing product contracts, schema ownership, or pretending that
scenario-family content is already available.

## Why this is next

The bounded corpus sweep showed a clear quality pattern across the imported
`10`-chapter slice:
- all bundles are structurally valid
- all bundles are backend-loadable
- `why_it_matters` currently duplicates `description`
- `when_to_use` is empty across the slice
- `tradeoffs` is empty across the slice

Before investing in `scenario drafts` or making recommendation rely on richer
content semantics, the importer should first stop producing empty or duplicate
concept fields where the source pages already contain usable cues.

## In scope

- mapper-side extraction improvements for `when_to_use`
- mapper-side extraction improvements for `tradeoffs`
- reduction of `why_it_matters == description` duplication
- provenance and confidence preservation for newly populated fields
- regression tests over representative fragment sets and exported packages
- corpus-quality remeasurement against the current bounded chapter slice

## Out of scope

- new product/backend APIs
- scenario draft extraction
- hint ladder extraction
- schema changes
- editorial approval workflows
- recommendation logic
- frontend changes

## Affected bounded contexts

- importer tooling
- content ingestion quality

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/04_content/content_schema.md`
- `tools/system-design-space-importer/docs/cli.md`
- `tools/system-design-space-importer/docs/source-policy.md`
- `implementation/roadmap.md`
- `implementation/status.md`

## Constraints

- stay within already-existing concept fields in the current content schema
- preserve explicit provenance and `review_required` posture
- prefer conservative extraction over fabricated richness
- generic overview pages should be allowed to remain sparse rather than receive
  invented `tradeoffs` or `when_to_use`
- exported bundles must remain backend-compatible

## Hidden assumptions

- many chapter pages contain usable usage/trade-off cues in prose, but the
  current mapper does not harvest them yet
- low-confidence LLM-assisted extraction is acceptable as draft content if
  provenance remains explicit and review-gated
- some pages will still legitimately produce empty fields after hardening
- reducing duplication is almost as important as filling empties because
  duplicated fields inflate apparent richness without adding meaning

## Architectural approaches considered

### Option A: Conservative heuristic extraction over existing fragments

- use current parsed fragments and fragment kinds
- derive `when_to_use` and `tradeoffs` from text cues in summaries/section
  bodies
- populate fields only when strong enough cues exist
- keep `why_it_matters` empty or distinct when no separate signal is found

Trade-offs:
- best fit for the current importer architecture
- deterministic and easier to debug
- lower recall than a more model-heavy approach
- less likely to hallucinate unsupported semantics

Decision:
- choose Option A as the primary posture

### Option B: LLM-heavy semantic fill for all concept fields

- ask a model to synthesize `why_it_matters`, `when_to_use`, and `tradeoffs`
  from normalized page text even when direct cues are weak

Trade-offs:
- could increase nominal field coverage quickly
- much higher risk of invented or overly generic outputs
- harder to validate and reason about field quality regressions

Rejected because:
- it would optimize for filled fields rather than trustworthy draft quality

### Option C: Skip concept-field hardening and jump straight to scenario drafts

- leave concept fields sparse
- focus all effort on `Scenario.prompt` and `canonical_axes`

Trade-offs:
- potentially more dramatic learner-facing payoff later
- builds on a weak concept substrate and makes scenario validation harder
- risks compounding one extraction gap with a larger one

Rejected because:
- concept-level semantic quality is the more immediate and lower-risk gap

## Proposed implementation shape

- extend the mapper with conservative cue extraction helpers for:
  - usage-fit phrases -> `when_to_use`
  - downside/cost/consistency/complexity cues -> `tradeoffs`
  - significance/impact framing -> `why_it_matters`
- keep provenance anchored to the supporting fragment ids used for each field
- preserve `review_required=True` for these fields in draft posture
- avoid copying `description` into `why_it_matters` when no distinct signal is
  found
- allow fields to remain empty if the source does not contain clear evidence

## TDD plan

### Phase 1: mapper unit tests first

Add or update importer tests before implementation.

Mapper contract:
- representative fragments with explicit usage cues produce non-empty
  `when_to_use`
- representative fragments with explicit downside/trade-off cues produce
  non-empty `tradeoffs`
- `why_it_matters` is not populated by blindly copying `description`
- generic fragments without clear support do not receive invented values
- provenance and `review_required` remain explicit

### Phase 2: package/export regression tests

Add or update tests around packaged/exported topic shapes.

Export contract:
- exported packages remain schema-valid
- field population changes are visible in the exported bundle snapshots
- existing package/review surfaces continue to emit explicit low-confidence
  signals where appropriate

### Phase 3: bounded corpus re-import and quality regression

Re-run the current bounded corpus slice after implementation.

Quality contract:
- `topics_with_any_when_to_use` becomes greater than `0`
- `topics_with_any_tradeoffs` becomes greater than `0`
- `topics_where_why_equals_description` drops below the current `10/10`
- schema validity does not regress
- backend compatibility remains intact

## Test contract

- extraction uses current importer artifacts only; no product-code coupling
- `when_to_use` is populated only from supported evidence
- `tradeoffs` is populated only from supported evidence
- `why_it_matters` is distinct or empty, not duplicated by default
- low-confidence provenance remains visible in exported bundles
- existing importer unit and smoke suites remain green

## Acceptance criteria

- at least some topics in the current bounded corpus gain non-empty
  `when_to_use`
- at least some topics in the current bounded corpus gain non-empty
  `tradeoffs`
- `why_it_matters == description` stops being universal across the corpus slice
- no schema or backend compatibility regressions are introduced
- recommendation and backend planning can rely on a meaningfully better concept
  substrate afterward

## Weak spots and assumption review

- weak spot: chapter pages may talk about concepts descriptively without
  cleanly separating use-cases and trade-offs; tests must distinguish “missing
  signal” from extraction failure
- weak spot: generic overview chapters may still remain sparse even after the
  slice; that is acceptable if the sparsity is honest
- hidden assumption: fragment-level heuristics will capture enough signal to
  improve corpus quality materially without needing a larger model-based pass
- hidden assumption: retaining `review_required=True` is sufficient to keep the
  draft posture honest even when more fields become populated
- no contradiction found with the v2.2 baseline because this slice enriches
  importer output quality without revising bounded-context ownership or product
  contracts

## ADR check

No ADR is required if this slice:
- preserves the existing content schema and ownership
- keeps draft provenance and review posture explicit
- does not revise product runtime, evaluation, or recommendation contracts

## Follow-on slice

After this slice, the next importer/content-quality slice should be:
- `006e. Scenario draft seeding`

That follow-on should start only after:
- concept field extraction is measurably improved
- the corpus is re-imported and re-audited
- the team can see whether the source material actually supports scenario
  extraction or still requires explicit authoring

## Definition of done

- explicit slice plan exists and is reviewed
- roadmap and status reflect the new execution order
- importer tests define and verify the new field extraction contract
- bounded corpus re-import shows measurable field coverage improvement
- backend compatibility remains unchanged

## Outcome

- importer now extracts non-empty `when_to_use` and `tradeoffs` from supported
  fragment cues instead of leaving them as universal placeholders
- `why_it_matters` is no longer populated by copying `description` by default
- extraction stays conservative:
  - title-anchored content window
  - `summary` and `section_body` only
  - limited number of matched values per field
- fixture-based mapper and export regressions are green
- bounded corpus regression improved from:
  - `0/10 -> 9/10` topics with non-empty `when_to_use`
  - `0/10 -> 8/10` topics with non-empty `tradeoffs`
  - `10/10 -> 0/10` topics where `why_it_matters == description`
- backend compatibility is unchanged over the re-imported corpus
