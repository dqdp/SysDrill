# Slice 002: Content Bundle Reader

## Status

- next

## Goal

Load exported topic bundles from disk into the backend through a deterministic,
file-based reader.

## Why this is on the critical path

This is the first real hand-off from tooling into the product runtime.

Without it, the backend has no stable way to consume the exported knowledge
artifacts and every later API slice risks binding to ad hoc file shapes.

This slice is intentionally about ingestion only. It must not silently redefine
draft exporter output as approved runtime truth.

## In scope

- backend file-based bundle reader
- bundle validation at read time
- deterministic topic catalog assembly
- preservation of provenance and validation metadata in memory
- explicit draft-ingestion posture for internal/dev use

## Out of scope

- database persistence
- write paths
- recommendation logic
- session runtime
- frontend integration
- final HTTP API surface
- `ExecutableLearningUnit` derivation
- any transformation that mixes `Content Kernel` ownership with `Learning Design`
  ownership

## Affected bounded contexts

- `Content Kernel`
- implementation-side backend infrastructure around content loading

## Source-of-truth references

- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- exported bundle contract in `tools/system-design-space-importer/docs/contracts.md`

## Proposed implementation shape

- `backend/src/.../content_bundle_reader.py`
- `backend/tests/test_content_bundle_reader.py`
- read from a configured export root
- return an in-memory catalog keyed by `topic_slug`
- require explicit configuration to allow draft bundle loading

## Test contract

- loads multiple valid bundles from a fixture export root
- rejects a bundle if `topic-package.yaml` is missing
- rejects a bundle if `validation-report.json` is missing
- rejects a bundle if `provenance.json` is missing
- rejects a bundle if `validation-report.schema_valid` is `false`
- rejects a bundle if directory name and `topic_slug` disagree
- rejects draft bundle loading when explicit draft-ingestion mode is disabled
- preserves UTF-8 content fields
- preserves provenance metadata for downstream debugging
- preserves review and validation metadata instead of flattening it away
- returns deterministically sorted topics
- does not traverse outside the configured export root

## Acceptance criteria

- backend can load exported bundles without a database
- loader behavior is deterministic and fail-closed
- bundle identity is stable on `topic_slug`
- no new product contract is invented in the reader
- draft bundle usage is explicitly gated and visible in configuration and return
  metadata

## Verification

- targeted backend unit tests for the reader
- `make verify-python`

## Definition of done

- reader exists and is covered by tests
- invalid bundles fail closed with explicit errors
- valid bundles produce a stable in-memory catalog ready for the next API slice
- reader does not collapse content loading into runtime or learning-design
  responsibilities

## Follow-up slice

- roadmap item `003. Content catalog API surface`
