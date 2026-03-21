# Status

## Current posture

Implementation has crossed from backend-only prototype work into a learner-visible
manual end-to-end shell.

The importer exporter MVP, content bundle reader, content catalog API, first
`ExecutableLearningUnit` materialization path, and manual runtime bootstrap are
complete. Deterministic review over that manual session loop is also complete,
GitHub-native verification plus bounded smoke coverage are now in place, and a
thin frontend shell now exercises the bounded launcher-to-review path. A
bounded corpus sweep and `Practice` prompt differentiation are now complete,
but importer analysis shows that current concept-field quality is still weak:
`when_to_use` and `tradeoffs` are empty across the slice and
`why_it_matters` largely duplicates `description`. Importer-side concept field
hardening is now complete as well. Conservative scenario draft seeding from
explicit example/problem pages is now complete too, including validator
hardening for emitted scenario completeness. Deterministic recommendation is
now complete as a process-local placeholder too: the primary frontend path can
request one rationale-bearing next step and start runtime from the returned
structured action, while the manual launcher remains as a bounded fallback.

## Prototype target

The shortest path to a working prototype is:
- manual session launch
- one bounded unit presentation from `ExecutableLearningUnit`
- one answer submission path
- append-only semantic events
- deterministic review output
- thin UI or equivalent demo path

Recommendation is intentionally not required for the first prototype milestone.

## Current active milestone

- `Milestone C. Content enrichment and guided next-step prototype`
- status: completed in current worktree

## Current active slice

- no post-`007` slice is selected yet
- next work should be planned explicitly from the now-completed Milestone C
  baseline

## Completed

### 001. Importer exporter MVP

Status:
- completed in commit `88250a4`

Delivered:
- bounded discovery
- bounded fetch policy
- `robots.txt` posture
- draft packaging
- materialized export bundles
- golden tests and real bounded run validation

### 002. Content bundle reader

Status:
- completed in current worktree

Delivered:
- deterministic file-based bundle reader in backend
- explicit draft-ingestion gate
- fail-closed bundle validation at read time
- UTF-8-safe loading of exported topic packages
- stable in-memory topic catalog keyed by `topic_slug`

### 003. Content catalog API surface

Status:
- completed in current worktree

Delivered:
- explicit app factory contract for content configuration
- read-only `GET /content/topics`
- read-only `GET /content/topics/{topic_slug}`
- API projection that avoids leaking raw provenance and filesystem paths
- fail-closed startup on invalid content configuration

### 003a. Content catalog hardening

Status:
- completed in current worktree

Delivered:
- fail-closed rejection when a configured export root yields zero topic bundles
- rejection of symlinked source/topic directories during bundle traversal
- explicit bundle payload type validation for required YAML/JSON sidecars
- regression tests for misconfigured roots, symlink traversal, and malformed
  payloads

### 004. Executable learning unit materialization

Status:
- completed in current worktree

Delivered:
- deterministic backend materializer for `concept_recall`
  `ExecutableLearningUnit` shapes
- bounded support for explicit `Study` and `Practice` mode/intent combinations
- fail-closed rejection for unsupported combinations such as `MockInterview`
- targeted unit tests for stable ids, mode-aware policy metadata, and
  non-mutating materialization

### 005. Session runtime and event log bootstrap

Status:
- completed in current worktree

Delivered:
- in-memory runtime service for manual single-unit session bootstrap
- manual runtime endpoints for session start, session read, and answer
  submission
- append-only semantic event emission at required runtime boundaries
- explicit evaluation hand-off payload assembled at answer submission time
- targeted tests for state transitions, error handling, and API wiring

### 005a. Bootstrap and runtime contract hardening

Status:
- completed in current worktree

Delivered:
- environment-configured ASGI bootstrap for content/runtime surfaces while
  preserving the explicit `create_app(...)` factory contract
- typed request validation for runtime POST endpoints to eliminate incidental
  `500` errors on malformed payloads
- fail-closed rejection of symlinked required bundle sidecar files
- runtime enforcement of unit `completion_rules.submission_kind`
- regression tests for bootstrap config, request validation, symlinked files,
  and submission-kind mismatches

### 006. Rule-first evaluation loop

Status:
- completed in current worktree

Delivered:
- deterministic rule-first evaluator for the bounded `concept_recall` unit
  family
- runtime transition from `evaluation_pending` to `review_presented`
- semantic event emission for `evaluation_attached` and `review_presented`
- explicit review retrieval path through the backend API
- source-of-truth documentation for the prototype `binding.concept_recall.v1`
- targeted evaluator, runtime, and API tests for deterministic reviewed outcomes

### 006a. Runtime and loader review hardening

Status:
- completed in current worktree

Delivered:
- process-local serialization of runtime state transitions for manual answer
  submission and evaluation attachment
- fail-closed rejection of symlinked configured export roots
- defensive topic summary projection for nullable nested bundle sections
- preserved health-only bootstrap when draft-loading env is malformed but no
  content root is configured
- regression tests for concurrency, export-root validation, nested nullable
  sections, and bootstrap env behavior

### 006b. GitHub CI and smoke verification

Status:
- completed in current worktree

Delivered:
- GitHub Actions workflow for blocking Python verification and bounded smoke
  checks
- root `Makefile` command surface for bootstrap, verification, and smoke runs
- fixture-based importer smoke coverage
- fixture-based backend manual reviewed loop smoke coverage
- green local verification for lint, format-check, unit tests, and smoke tests

### 008. Practice frontend shell

Status:
- completed in current worktree

Delivered:
- minimal TypeScript frontend shell under `frontend/`
- narrow backend launcher endpoint for backend-owned manual launch options
- learner-visible launcher, answer, evaluation, and review flow over the
  existing manual reviewed loop
- frontend verification commands wired into the root `Makefile`
- GitHub workflow coverage for frontend test and build verification
- browser-level demo verification against the local backend and frontend dev
  servers

### 007. Recommendation placeholder

Status:
- completed in current worktree

Delivered:
- process-local deterministic recommendation engine over the current
  executable concept-action surface
- recommendation API returning one versioned, rationale-bearing structured
  action instead of a raw `unit_id`
- runtime entrypoint that starts a session from the chosen recommendation
  action after legality and resolvability checks
- append-only runtime interaction events only for
  `recommendation_accepted` / `recommendation_completed`, while
  generated/shown tracking remains internal to the recommendation store
- recommendation-first frontend path with the manual launcher preserved as a
  bounded fallback
- green backend, frontend, and smoke verification

## Planned next

### 006c0. Bounded corpus acquisition and quality sweep

Status:
- completed in current worktree

Intent:
- replace the current tiny imported sample with a wider bounded corpus and
  produce a quality summary over what the importer actually materializes

Guardrails:
- keep crawl scope bounded and chapter-only
- keep the resulting export root separate from fixtures
- do not change product contracts during this slice

Delivered:
- bounded discovery from the site root
- a curated `10`-chapter technical corpus slice under
  `.tmp/sds-importer/corpus-slice-01/exports/`
- quality sweep confirming schema-valid but recall-only draft bundles
- backend compatibility verification over the new export root

### 006c. Practice prompt expansion

Status:
- completed in current worktree

Intent:
- enrich `Practice` prompt framing from existing concept metadata so that the
  current launcher and future recommendation layer operate over a more
  meaningful action difference than “same concept, nearly same prompt”

Guardrails:
- stay inside `concept_recall`
- keep `binding.concept_recall.v1`
- avoid introducing scenario-family semantics early

Delivered:
- richer `Practice` prompt materialization over existing concept metadata
- deterministic fallback when optional prompt fields are empty
- unchanged `concept_recall` binding, runtime transitions, and API payloads
- regression coverage at materializer, runtime service, and API layers

### 007. Recommendation placeholder

Status:
- completed in current worktree

Intent:
- replace manual launch as the main learner path with one bounded,
  deterministic recommendation action over the now-wider and better-differentiated
  concept action space

Guardrails:
- recommendation returns a structured action, not a raw `unit_id`
- runtime remains the owner of action resolution and session creation
- learner-state mutation still does not bypass events or evaluation

Delivered:
- deterministic bootstrap recommendation selection over current launchable
  concept actions
- runtime start-from-recommendation contract without synthetic pre-session
  `session_id`
- recommendation-generated/shown tracked in process-local records, not forced
  into the runtime event log
- recommendation-first frontend happy path while preserving manual fallback

### 006d. Concept field extraction hardening

Status:
- completed in current worktree

Intent:
- improve importer-side concept field extraction so the draft corpus contains
  less duplicated semantics and more usable `when_to_use` / `tradeoffs`
  coverage

Guardrails:
- preserve explicit provenance and `review_required` posture
- prefer sparse-but-honest output over invented semantic richness
- do not change backend or product contracts during this slice

Delivered:
- non-empty `when_to_use` coverage on `9/10` topics in the bounded corpus
- non-empty `tradeoffs` coverage on `8/10` topics in the bounded corpus
- `why_it_matters == description` reduced from `10/10` to `0/10`
- unchanged backend compatibility over the re-imported corpus

### 006e. Scenario draft seeding

Status:
- completed in current worktree

Intent:
- seed the first conservative `Scenario` drafts from explicitly
  example/interview/problem-like source pages

Guardrails:
- fail closed on ordinary concept chapters
- require complete scenario field coverage for any emitted scenario
- preserve provenance and review posture

Delivered:
- first bounded scenario seeding path from explicit source material:
  `troubleshooting-example -> scenario.troubleshooting-example`
- fail-closed behavior for ordinary concept pages and interview-format theory
  pages without a concrete problem statement
- validator enforcement for required scenario field completeness
- package/export preservation of scenario-bearing bundles
- bounded live-source verification showing one schema-valid seeded scenario and
  no scenario regression on `caching-strategies`

## Known risks

- exported bundles are still review-first artifacts, not approved canonical content
- export is intentionally non-destructive, so stale export directories from older runs may persist
- backend integration must not infer new contracts from exporter internals
- backend integration must not bypass the future `Learning Design ->
  ExecutableLearningUnit -> Runtime` seam
- runtime work must not skip append-only semantic event logging

## Current blockers

- none

## Exit condition for current phase

The current phase is complete when:
- concept-field extraction quality has improved over the current placeholder
  baseline
- at least one explicit source page can yield a valid seeded scenario draft
- recommendation can then return one bounded next-step action and runtime can
  start from that action without changing the manual prototype loop semantics
  already demonstrated in Milestone B
