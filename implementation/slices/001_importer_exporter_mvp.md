# Slice 001: Importer Exporter MVP

## Status

- completed

## Goal

Turn bounded upstream content from `system-design.space` into usable exported
topic bundles that can seed the main project.

## Why this was on the critical path

The main project needed real data before backend and frontend work could start
against stable content artifacts.

## In scope

- bounded discovery
- bounded HTTP fetch policy
- `robots.txt` posture
- deterministic extraction and mapping
- validation
- materialized export bundles

## Out of scope

- direct writes into runtime storage
- editorial approval workflow
- full semantic authoring automation

## Affected bounded contexts

- none in the core product runtime
- isolated operational importer tool only

## Source-of-truth references

- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/04_content/authoring_model_v1.md`
- tool-local contracts under `tools/system-design-space-importer/docs/`

## Test contract

- bounded discovery only keeps allowed URLs
- fetch preserves policy metadata and respects stronger crawl-delay
- export writes `topic-package.yaml`, `provenance.json`, and `validation-report.json`
- export fails closed on invalid validation reports
- mapper uses stable URL-derived identity instead of title-derived slugging

## Verification

- `make verify-python`
- bounded real run against `system-design.space`

## Definition of done

- exported bundles exist and are readable
- output is stable enough for snapshot testing
- real bounded run produces usable topic packages

## Residual risks

- bundles remain review-first artifacts
- export root can retain stale directories from older runs
