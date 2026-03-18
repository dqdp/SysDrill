# Status

## Current posture

Implementation has crossed from tooling into a usable read-only backend content surface.

The importer exporter MVP, content bundle reader, and content catalog API
surface are complete. The next critical path item is materializing bounded
`ExecutableLearningUnit` shapes without collapsing `Content Kernel` and
`Learning Design`.

## Current active slice

- roadmap item `004. Executable learning unit materialization`
- next code change requires a new explicit slice file before implementation

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

Phase 3 hand-off is complete when the backend can materialize bounded
`ExecutableLearningUnit` shapes from loaded content and learning-design inputs
without bypassing the `Content Kernel -> Learning Design -> Runtime` seam.
