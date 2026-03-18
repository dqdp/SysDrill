# Status

## Current posture

Implementation has crossed from tooling into a usable read-only backend content surface.

The importer exporter MVP, content bundle reader, content catalog API, first
`ExecutableLearningUnit` materialization path, and manual runtime bootstrap are
complete. The next critical path item is deterministic review output over that
manual session loop.

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
- fast-path order: `005 -> 006 -> 008`

## Current active slice

- roadmap item `006. Rule-first evaluation loop`
- next code change should create an explicit slice file for deterministic review
  output over the manual runtime path

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
