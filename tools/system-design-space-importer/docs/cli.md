# CLI Contract

## Purpose

The importer CLI should make each pipeline stage independently runnable and
debuggable.

## Command set

### `discover`

Input:
- seed URL or seed file
- allowlist profile

Output:
- manifest of candidate URLs

Behavior:
- if the seed is already an allowed chapter URL, it is kept as the only target
- if the seed is an index page, discovery extracts only path-allowed links
- `max_pages` is applied after filtering and deduplication
- for allowed HTTP seeds, discovery also records `robots_policy` in the manifest

Example shape:
```text
importer discover --seed https://system-design.space/ --profile chapters_only
```

### `fetch`

Input:
- discovery manifest or explicit URL list

Output:
- stored `SourceDocument` artifacts
- raw HTML snapshots
- normalized text snapshots

Example shape:
```text
importer fetch --run-id 2026-03-18T15-10-00Z
```

### `extract`

Input:
- fetched source documents

Output:
- `ParsedSourceFragment[]`

Example shape:
```text
importer extract --run-id 2026-03-18T15-10-00Z
```

### `map`

Input:
- parsed fragments

Output:
- `SemanticDraft`

Example shape:
```text
importer map --run-id 2026-03-18T15-10-00Z
```

### `validate`

Input:
- semantic drafts or packaged drafts

Output:
- `ValidationReport`

Example shape:
```text
importer validate --run-id 2026-03-18T15-10-00Z
```

### `package`

Input:
- semantic drafts
- validation results

Output:
- `DraftTopicPackage`

Example shape:
```text
importer package --run-id 2026-03-18T15-10-00Z
```

### `export`

Input:
- packaged drafts
- validation reports
- fetched source documents
- discovery manifest

Output:
- `exports/<source>/<topic>/topic-package.yaml`
- `exports/<source>/<topic>/provenance.json`
- `exports/<source>/<topic>/validation-report.json`

Behavior:
- materializes a downstream-readable bundle outside the run-local artifact tree
- fails closed if `validation-report.schema_valid = false`
- preserves pointers back to run artifacts for review and replay

Example shape:
```text
importer export --run-id 2026-03-18T15-10-00Z
```

### `run`

Input:
- seed URL or explicit bounded source set
- optional stage flags

Behavior:
- executes the full bounded pipeline

Output:
- full run artifact directory
- materialized export bundles

Example shape:
```text
importer run --seed https://system-design.space/ --profile chapters_only
```

## Operational flags

Recommended global flags:
- `--run-id`
- `--out-dir`
- `--profile`
- `--max-pages`
- `--timeout-s`
- `--max-retries`
- `--rate-limit`
- `--rate-limit-ms`
- `--browser-fallback`
- `--fail-fast`

## Exit semantics

- `0`: successful stage completion
- non-zero: stage failure or validation failure

Validation failures should remain inspectable through output artifacts and should
not be hidden behind a generic process error.
