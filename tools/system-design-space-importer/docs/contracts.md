# Importer Contracts

## Contract stance

The importer uses explicit intermediate artifacts so that each stage can be:
- replayed
- tested
- diffed
- reviewed

## SourceDocument

Represents one fetched upstream page.

Required fields:
- `document_id`
- `source_name`
- `source_url`
- `fetched_at`
- `fetch_mode`
- `http_status`
- `content_type`
- `source_hash`
- `raw_html_path`
- `normalized_text_path`
- `parser_version`

Optional fields:
- `canonical_url`
- `discovered_from`
- `charset`
- `locale`
- `fetch_metadata`

Rules:
- `source_hash` must reflect normalized main content, not full page chrome
- failed fetches may be recorded, but may not proceed to extraction
- HTTP fetches should preserve bounded policy metadata such as timeout, retry,
  and rate-limit settings
- effective rate limiting should preserve any stronger `robots.txt` crawl-delay
  constraint in output metadata

## Discovery manifest

The discovery stage must persist a manifest containing:
- `run_id`
- `created_at`
- `profile`
- `seed`
- `urls`
- `fetch_policy`
- `discovery_policy`
- `robots_policy`

Rules:
- `robots_policy` may be `not_applicable_local_file` for local fixtures
- index-page discovery should persist only path-allowed, deduplicated URLs

## ParsedSourceFragment

Represents one extracted fragment from a fetched source document.

Required fields:
- `fragment_id`
- `document_id`
- `kind`
- `heading_path`
- `order`
- `text`
- `links`
- `fragment_hash`

Optional fields:
- `source_selector`
- `dom_path`

Allowed `kind` values:
- `title`
- `summary`
- `section_heading`
- `section_body`
- `bullet_list`
- `reference_link`
- `related_link`
- `meta`

Rules:
- fragment order must be stable for the same source content
- fragments must preserve enough source traceability for editorial review

## ProvenanceRef

Represents the trace from a draft field back to source evidence.

Required fields:
- `document_id`
- `fragment_ids`
- `extraction_mode`
- `confidence`

Optional fields:
- `notes`

Allowed `extraction_mode` values:
- `rule`
- `llm_assisted`
- `manual`

Rules:
- every exported draft field must have at least one provenance reference
- low-confidence fields must be marked review-required

## SemanticDraft

Represents a machine-produced semantic interpretation of one or more source
documents before editorial approval.

Required fields:
- `draft_id`
- `source_document_ids`
- `inferred_topic_slug`
- `mapper_version`
- `concepts`
- `patterns`
- `scenarios`
- `hint_ladders`
- `unresolved_fragment_ids`
- `warnings`

Rules:
- unresolved fragments must remain visible
- semantic draft may be incomplete
- semantic draft is not authoritative content

## DraftTopicPackage

Represents a reviewable authoring package produced by the importer.

Required fields:
- `package_id`
- `topic_slug`
- `generated_at`
- `tool_version`
- `source_document_ids`
- `canonical_content`
- `canonical_support`
- `review`
- `validation_summary`

Optional fields:
- `learning_design_drafts`

Rules:
- package output remains draft until approved
- learning-design output is optional and advisory in v1
- review status must be explicit

## ProvenanceSidecar

Represents the audit trail for one exported topic package.

Required fields:
- `package_id`
- `topic_slug`
- `run_id`
- `source_name`
- `source_document_ids`
- `manifest`
- `documents`
- `artifacts`

Rules:
- provenance must preserve run-level discovery and fetch policy metadata
- provenance must point back to the exact run artifacts used to materialize the
  exported package
- documents included in provenance must be the fetched `SourceDocument`
  artifacts, not a rewritten summary

## Export bundle

Represents the downstream-readable output of the importer.

Required files per topic:
- `topic-package.yaml`
- `provenance.json`
- `validation-report.json`

Recommended path shape:
- `exports/<source-name>/<topic-slug>/...`

Rules:
- export is a materialization step over existing run artifacts
- invalid validation reports must fail closed and block export
- `topic-package.yaml` should remain human-reviewable
- sidecar JSON files should remain machine-readable and diff-friendly

## ValidationReport

Represents validation output for one semantic draft or packaged draft.

Required fields:
- `package_id`
- `checked_at`
- `schema_valid`
- `errors`
- `warnings`
- `low_confidence_paths`
- `missing_required_paths`

Rules:
- invalid packages must fail closed
- warnings must not be dropped from review surfaces

## Manual-review-first fields

The following fields should default to review-required in v1:
- `content_difficulty_baseline`
- `canonical_axes`
- `anti_shortcuts`
- `hint_ladder.levels`
- any learning-design recommendations
