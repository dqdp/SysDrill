# Slice 006c0: Bounded Corpus Acquisition And Quality Sweep

## Status

- completed in current worktree

## Goal

Acquire a wider but still bounded real-content corpus from `system-design.space`
before changing backend learning-design behavior.

The purpose of this slice is to replace conclusions drawn from two tiny draft
bundles with evidence from a materially larger chapter set, while preserving
the importer boundary and existing backend contracts.

## Why this is on the critical path

Current product feedback is dominated by an undersized corpus:
- only a small number of imported topics are available
- current prompts and launcher behavior are being judged on sparse draft data
- changing `Practice` before inspecting a larger corpus risks optimizing for a
  non-representative sample

Before changing backend prompt materialization, the project should gather a
larger bounded corpus and inspect what the importer actually produces at scale.

## In scope

- bounded chapter discovery from `https://system-design.space/`
- selection of a curated high-value chapter batch from the discovered manifest
- full importer pipeline runs for that bounded batch
- export of a separate corpus slice root under `.tmp/`
- a quality sweep over exported bundles and validation reports
- a backend launchability check against the new export root

## Out of scope

- unbounded crawling
- product-code changes in backend or frontend
- recommendation or runtime redesign
- editorial approval of imported bundles
- schema or contract changes
- production publishing of imported content

## Affected bounded contexts

- importer tooling
- content ingestion verification
- backend content-loading verification

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `tools/system-design-space-importer/docs/cli.md`
- `tools/system-design-space-importer/docs/source-policy.md`
- `implementation/roadmap.md`
- `implementation/status.md`

## Constraints

- crawl scope must remain bounded and chapter-only
- importer must respect the documented polite-fetch posture
- the resulting corpus must live in a separate export root from fixtures
- no backend contract may start depending on importer run-internal artifacts
- findings must distinguish schema-validity from content richness

## Hidden assumptions

- schema-valid draft bundles may still be pedagogically weak or sparse
- some chapters may produce nearly empty optional fields even when import
  succeeds technically
- a curated chapter batch gives better signal than a raw first-N crawl
- imported draft text remains suitable for dev/demo evaluation when explicitly
  loaded behind `allow_draft_bundles=True`

## Architectural approaches considered

### Option A: One large bounded crawl from the site index

- run discovery from the site root
- import the first bounded set of discovered chapter URLs

Trade-offs:
- fastest way to gather more data
- lower control over topic quality and relevance
- higher risk that results are dominated by weak or repetitive chapters

### Option B: Hand-pick a small set of direct chapter seeds only

- skip broad discovery
- import only a few known high-value technical chapters

Trade-offs:
- high signal per imported topic
- easiest to interpret
- may miss structural importer issues that only appear on a wider slice

### Option C: Bounded discovery plus curated batch selection

- run bounded discovery from the site root
- inspect the discovered manifest
- select a curated `10-15` chapter batch
- run the full importer pipeline only for that batch

Trade-offs:
- best balance between coverage and quality control
- slightly slower than direct seed import
- produces a more trustworthy basis for the next backend slice

Decision:
- choose Option C

## Proposed implementation shape

- run a bounded discovery pass from the site root
- derive a curated technical chapter batch from the manifest
- run full `sds-importer run` for each selected chapter with explicit run ids
- export into a dedicated corpus root under:
  `.tmp/sds-importer/corpus-slice-01/exports/`
- summarize corpus quality from exported `topic-package.yaml` and
  `validation-report.json`
- load the new export root through the backend to measure launchable-unit count
  and verify contract compatibility

## Verification-first plan

### Phase 1: discovery contract

Discovery contract:
- root-seed discovery succeeds with bounded chapter-only scope
- manifest records a non-trivial chapter set
- discovery remains within the documented source policy

### Phase 2: curated corpus acquisition

Acquisition contract:
- at least `10` chapters are selected from discovery output
- each selected chapter runs through the full importer pipeline
- exported bundles land in a dedicated corpus root
- failures remain inspectable per run rather than hidden

### Phase 3: quality sweep

Quality contract:
- report how many bundles are schema-valid
- report coverage of key concept fields:
  `description`, `why_it_matters`, `when_to_use`, `tradeoffs`
- report how many bundles emit warnings such as missing scenario drafts or hint
  ladders
- report how many bundles expose only `recall` candidate card types

### Phase 4: backend compatibility check

Backend contract:
- backend can load the new export root without contract changes
- launchable units can be materialized from the new corpus
- findings clearly separate “more content imported” from “better practice units”

## Acceptance criteria

- a bounded real-content corpus larger than the current two-topic sample exists
  under `.tmp/`
- there is a concrete quality summary over the imported batch
- backend launchability against the new export root is verified
- roadmap and status reflect this slice as the immediate next step

## Weak spots and assumption review

- weak spot: chapter coverage can still skew toward concept summaries rather
  than richer scenarios because the upstream site structure itself is summary
  heavy
- weak spot: importer success does not imply good learner-facing prompts; the
  quality sweep must explicitly separate structural validity from pedagogical
  richness
- hidden assumption: current fetch policy is operationally acceptable for a
  bounded `10-15` chapter batch; if the site pushes back, scope should narrow
- no contradiction found with the v2.2 baseline because this slice changes
  evidence quality, not architecture or product contracts

## ADR check

No ADR is required if this slice:
- keeps importer scope bounded
- does not revise product contracts
- does not change bounded-context ownership

## Definition of done

- explicit slice plan exists and is reviewed
- roadmap and status reflect the new execution order
- a bounded corpus slice has been imported successfully
- a quality sweep summary exists
- backend compatibility against the new export root is verified

## Outcome

- a bounded corpus slice with `10` technical chapter bundles now exists under
  `.tmp/sds-importer/corpus-slice-01/exports/`
- all `10` exported topic bundles are schema-valid and backend-loadable
- all `10` bundles currently remain `recall`-only and emit the same structural
  warnings:
  `canonical axes were not inferred`, `no scenario draft was emitted`,
  `no hint ladders were generated`
- all `10` bundles contain non-empty `description` and `why_it_matters`
  coverage, but `when_to_use` and `tradeoffs` remain empty across the slice
- backend materializes `10` launchable units for each currently supported
  `Study` and `Practice` mode/intent combination against this corpus root
