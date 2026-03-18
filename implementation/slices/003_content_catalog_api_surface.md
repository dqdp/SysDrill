# Slice 003: Content Catalog API Surface

## Status

- completed

## Goal

Expose the loaded content catalog through a minimal read-only FastAPI surface.

## Why this is on the critical path

The backend already has a deterministic file-based content reader. The next
step is to make that catalog available to the frontend and to later runtime
flows without introducing write paths, database persistence, or session logic.

## In scope

- read-only content catalog endpoints
- backend wiring from content bundle reader into FastAPI
- deterministic response ordering
- explicit draft-ingestion configuration for API startup
- fail-closed startup behavior when configured content loading is invalid
- a narrow response DTO that does not expose raw exporter/internal file paths

## Out of scope

- database persistence
- recommendation logic
- `ExecutableLearningUnit` derivation
- session creation
- answer submission
- evaluation
- frontend data fetching code

## Affected bounded contexts

- `Content Kernel`
- `web_api / ui`

## Source-of-truth references

- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- `implementation/slices/002_content_bundle_reader.md`

## Proposed implementation shape

- extend `backend/src/sysdrill_backend/app.py`
- add a thin content-catalog adapter module only if needed
- reuse `content_bundle_reader` instead of duplicating bundle parsing
- read from one explicitly configured active export root only

## App factory contract

The minimal app factory should accept explicit content configuration rather than
implicit environment discovery.

Expected shape:
- `create_app(content_export_root=..., allow_draft_bundles=...)`

Rationale:
- startup behavior becomes deterministic in tests
- no hidden dependency on shell or process environment
- fail-closed content loading stays explicit

## Active content root posture

- the API must not auto-discover the "latest" exporter output
- the configured export root must be an explicitly chosen active content snapshot
- the API must not treat an accumulating exporter workspace as a valid active
  content root by default
- if that guard cannot be enforced mechanically in this slice, it must at least
  be explicit in startup configuration and tests

## Endpoint proposal

- `GET /health`
- `GET /content/topics`
- `GET /content/topics/{topic_slug}`

## Response posture

- response data is read-only and derived from loaded topic bundles
- preserve stable topic identity on `topic_slug`
- keep review/validation metadata available for internal API consumers
- do not expose provenance payloads or filesystem paths in the API contract

### `GET /content/topics` response shape

Each item should include only summary fields needed for catalog display:
- `topic_slug`
- `display_title`
- `concept_count`
- `pattern_count`
- `scenario_count`
- `review_status`
- `schema_valid`

Temporary title derivation rule for this slice:
- use `canonical_content.concepts[0].title.value` if present
- otherwise use `canonical_content.scenarios[0].title.value` if present
- otherwise fall back to `topic_slug`

### `GET /content/topics/{topic_slug}` response shape

The detail surface may include:
- `topic_slug`
- `bundle_source_name`
- `is_draft_bundle`
- `source_document_ids`
- `canonical_content`
- `canonical_support`
- `review`
- `validation_summary`

The detail surface should not include:
- raw `provenance`
- manifest internals
- run-local filesystem paths
- nested provenance payloads inside content fields

For this slice, `canonical_content` and `canonical_support` should therefore be
returned as API projections with plain canonical values only, not raw exporter
field wrappers.

## Test contract

- `GET /content/topics` returns deterministically sorted topics
- `GET /content/topics` returns UTF-8 content safely
- `GET /content/topics` returns only summary fields, not raw bundle payloads
- `GET /content/topics` uses the documented display-title fallback rule
- `GET /content/topics/{topic_slug}` returns one topic when present
- `GET /content/topics/{topic_slug}` returns `404` for unknown topic
- `GET /content/topics/{topic_slug}` does not expose provenance payloads or
  filesystem paths
- app factory takes explicit content configuration arguments instead of relying
  on implicit environment discovery
- app startup fails closed when configured export root is invalid
- app startup fails closed when draft bundle loading is disabled for draft-only
  bundles
- app startup fails closed when the configured root is not an explicitly chosen
  active content root according to this slice's startup policy
- `GET /health` remains unaffected by the content endpoints when startup
  succeeds with a valid content configuration
- API surface does not mutate catalog state

## Acceptance criteria

- backend serves a stable read-only content catalog from exported bundles
- content loading stays delegated to the bundle reader
- no new write path or runtime orchestration behavior is introduced
- startup policy around active export root is explicit and deterministic
- endpoint shapes are narrow enough to support the next slice without locking
  us into a premature public API

## Verification

- targeted FastAPI tests for content endpoints
- `make verify-python`

## Definition of done

- content catalog endpoints exist and are covered by tests
- invalid content configuration fails closed
- the API is ready for the later `ExecutableLearningUnit` slice without reading
  raw exporter files directly in runtime code

## Outcome

- implemented as a read-only FastAPI surface over the existing bundle reader
- verified through targeted endpoint tests and `make verify-python`

## Follow-up slice

- roadmap item `004. Executable learning unit materialization`
