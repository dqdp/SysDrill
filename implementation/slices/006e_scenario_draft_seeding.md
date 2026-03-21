# Slice 006e: Scenario Draft Seeding

## Status

- completed in current worktree

## Goal

Seed conservative `Scenario` drafts from importer output only when the source
page is explicitly problem-like or interview-example-like.

This slice should produce the first bounded `Scenario` content objects without:
- synthesizing system-design problems from ordinary concept chapters
- collapsing `Content Kernel` and `Learning Design`
- weakening provenance or review posture

## Why this is next

The current importer now produces meaningfully better concept fields, but the
content kernel still has:
- `0` scenarios in the bounded technical corpus
- no canonical axes
- no canonical follow-up candidates

At the same time, source inspection shows that the upstream site is mostly
concept-heavy. The importer does not currently surface explicit pages like
`url-shortener` or `rate-limiter`, but some pages such as
`troubleshooting-example` are plausibly scenario-like.

This means the next honest step is not broad scenario generation. It is narrow
scenario seeding from explicitly problem/example/interview-style pages only,
with the first target restricted to pages that contain both:
- an explicit interview/example framing
- a concrete incident/problem section with operational cues

## In scope

- conservative scenario detection for explicit example/problem/interview pages
  that also expose a concrete incident/problem statement
- scenario draft extraction for required `Scenario` fields
- provenance-bearing scenario field population
- validator hardening so emitted scenarios must include required fields
- regression tests proving concept pages do not silently become scenarios
- bounded verification on representative scenario-like source pages

## Out of scope

- generating scenarios from ordinary concept chapters
- scenario-family evaluation or runtime work
- hint ladder generation
- follow-up runtime orchestration
- frontend changes
- recommendation changes
- schema ownership changes

## Affected bounded contexts

- importer tooling
- content ingestion quality
- content-kernel draft packaging

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- `docs/02_domain/domain_model.md`
- `docs/02_domain/learning_design_boundary.md`
- `docs/03_architecture/scenario_rubric_binding_v1.md`
- `implementation/roadmap.md`
- `implementation/status.md`

## Constraints

- scenario seeding must be fail-closed
- ordinary concept pages must remain concept-only if there is no explicit
  scenario/problem signal
- seeded scenarios must include all required schema fields:
  `id`, `title`, `prompt`, `content_difficulty_baseline`,
  `expected_focus_areas`, `canonical_axes`, `canonical_follow_up_candidates`
- provenance and `review_required` posture must remain explicit
- no product/backend contract changes are allowed in this slice

## Hidden assumptions

- the current source corpus may support only a very small number of scenario
  drafts, and that is acceptable
- pages such as `troubleshooting-interview` may look interview-like but still
  remain concept-only because they describe a format rather than a concrete
  problem statement
- some required scenario fields will need conservative heuristic seeding rather
  than exact extraction, but they must still remain review-gated
- the importer's current validation logic is too weak for scenario emission and
  must be tightened inside this slice

## Architectural approaches considered

### Option A: Seed scenarios only from explicitly scenario-like pages

- detect pages whose title/summary/body clearly indicate interview examples,
  troubleshooting cases, or design tasks
- extract one conservative scenario draft from those pages
- keep concept chapters concept-only

Trade-offs:
- best match to content-kernel ownership
- minimizes hallucinated scenario objects
- likely low recall on the current source corpus
- honest even if the result is only `1-2` scenario drafts

Decision:
- choose Option A

### Option B: Synthesize scenarios from concept pages

- transform concept chapters like `caching-strategies` or `load-balancing`
  into prompts such as “design a caching layer” or “design load balancing”

Trade-offs:
- higher scenario coverage quickly
- violates the boundary that `Scenario.prompt` is content, not pedagogical
  synthesis
- risks producing pseudo-scenarios with weak canonical axes

Rejected because:
- it would invent content instead of extracting it

### Option C: Skip importer seeding and require hand-authored scenario files

- do not emit any scenarios from importer
- rely on later manual authoring for scenario coverage

Trade-offs:
- highest quality ceiling
- blocks empirical learning about how much scenario signal the source contains
- delays content-kernel progress unnecessarily

Rejected because:
- a conservative importer experiment is still worthwhile before committing to
  manual-only scenario authoring

## Proposed implementation shape

- add scenario-like page detection based on explicit cues such as:
  `example`, `interview`, `troubleshooting`, `design task`, or equivalent
  Russian phrasing in title/summary/near-title content
- require an additional concrete-problem signal such as:
  `incident`, `symptom`, `alert`, `legend`, or incident/problem bullets
- when a page qualifies, emit one scenario draft with:
  - stable `id`
  - `title` from the page title
  - `prompt` from summary plus the strongest scenario-setting body fragments
    from legend/incident sections
  - conservative `content_difficulty_baseline`
  - `expected_focus_areas` from strongest domain/problem fragments
  - `canonical_axes` from selected operational/architectural dimensions
    explicitly named in incident/problem bullets
  - `canonical_follow_up_candidates` from explicit depth cues if present
- keep all scenario fields provenance-bearing; keep semantic scenario fields
  review-gated while allowing deterministic identity fields to stay
  source-derived
- emit no scenario if required fields cannot be populated honestly
- tighten validator logic so any emitted scenario draft must contain all
  required scenario fields

## TDD plan

### Phase 1: mapper scenario detection tests

Mapper contract:
- explicit example/interview-style fragments produce exactly one scenario draft
- ordinary concept pages still produce zero scenario drafts
- interview-format pages without a concrete problem statement still produce zero
  scenario drafts
- emitted scenario ids are stable and topic-derived
- emitted scenario fields are provenance-bearing
- emitted semantic scenario fields are review-gated

### Phase 2: validator hardening tests

Validator contract:
- a draft containing a scenario missing required fields fails schema validation
- a valid seeded scenario passes validation
- absence of scenarios remains allowed

### Phase 3: export regression tests

Export contract:
- exported bundles preserve scenario drafts when present
- existing concept-only fixture exports remain compatible
- scenario-bearing fixture export shape is deterministic

### Phase 4: bounded source verification

Verification contract:
- a representative scenario-like page such as `troubleshooting-example`
  yields a scenario draft
- a representative concept page such as `caching-strategies` still yields no
  scenario draft
- backend loading of the exported bundle remains unaffected

## Test contract

- scenario extraction is explicit and conservative
- concept pages do not become scenarios by accident
- interview-format concept pages do not become scenarios by accident
- every emitted scenario has all required schema fields
- provenance remains attached to scenario fields
- importer unit tests and smoke tests remain green
- backend compatibility remains unchanged

## Acceptance criteria

- at least one explicitly scenario-like source page yields one valid scenario
  draft
- representative concept pages still emit zero scenarios
- representative interview-format theory pages still emit zero scenarios
- validator rejects malformed scenario drafts
- exported bundles remain schema-valid and backend-compatible
- no product/runtime/recommendation contracts are changed

## Weak spots and assumption review

- weak spot: current source corpus may simply not contain enough explicit
  problem pages for broad scenario coverage; success for this slice may still be
  `1-2` valid scenario drafts
- weak spot: the current source contains noisy architecture fragments and UI
  helper text; extraction must stay restricted to summary plus explicit
  legend/incident/problem sections
- weak spot: `canonical_axes` and follow-up candidates are semantically heavy;
  heuristics must stay conservative and review-gated
- hidden assumption: a scenario-bearing draft bundle can still be useful even if
  no runtime/evaluation path consumes it yet
- hidden assumption: validator hardening is required inside this slice because
  current validation does not enforce scenario field completeness
- hidden assumption: validator will remain stricter for `Scenario` than for
  legacy `Concept` completeness in this slice; broader schema-hardening remains
  separate technical debt
- no contradiction found with the v2.2 baseline as long as scenario prompts are
  extracted only from explicit source material rather than synthesized from
  concept pages

## ADR check

No ADR is required if this slice:
- preserves content-kernel ownership of scenario objects
- keeps scenario seeding conservative and provenance-bearing
- does not revise runtime, evaluation, or recommendation contracts

## Definition of done

- explicit slice plan exists and is reviewed
- roadmap and status reflect the new execution order
- mapper tests define scenario seeding vs non-seeding behavior
- validator tests enforce required scenario field completeness
- a bounded verification run proves at least one honest scenario seed path
- backend compatibility remains unchanged

## Outcome

- importer now emits the first conservative `Scenario` draft for explicit
  example/problem material:
  - `troubleshooting-example -> scenario.troubleshooting-example`
- ordinary concept pages remain concept-only:
  - `caching-strategies -> 0 scenarios`
- interview-format theory pages remain concept-only when they do not expose a
  concrete problem statement
- validator now rejects emitted scenarios that omit required fields or leave
  required list fields empty
- package/export flow preserves scenario-bearing bundles without changing
  backend contracts
- bounded live-source verification shows:
  - `troubleshooting-example` exports one schema-valid, review-gated scenario
  - `caching-strategies` still exports zero scenarios

## Residual risks

- seeded scenario fields remain heuristic and review-gated, not editorially
  approved canonical content
- the current source corpus still appears sparse for broad scenario coverage;
  this slice proves a narrow path, not a rich scenario corpus
- runtime and evaluation remain `concept_recall`-only, so the new `Scenario`
  objects are content-kernel assets for future slices rather than currently
  executable learner flows
