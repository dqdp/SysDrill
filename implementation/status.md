# Status

## Current posture

Implementation has crossed from tooling into a usable read-only backend content surface.

The importer exporter MVP, content bundle reader, content catalog API, first
`ExecutableLearningUnit` materialization path, and manual runtime bootstrap are
complete. Deterministic review over that manual session loop is also complete,
and GitHub-native verification plus bounded smoke coverage are now in place.
The next critical path item is a thin frontend or equivalent demo path over the
verified backend loop.

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

- `Milestone B. Manual end-to-end prototype`
- fast-path order: `005 -> 006 -> 006b -> 008`

## Current active slice

- roadmap item `008. Practice frontend shell`
- next code change should connect a thin UI or equivalent demo path to the
  now-verified manual runtime loop

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

The current phase is complete when one learner can manually launch a bounded
session over a materialized `ExecutableLearningUnit`, submit an answer, emit
append-only semantic events, and receive deterministic review through the
backend plus a thin UI or equivalent demo path.
