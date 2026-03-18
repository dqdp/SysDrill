# Test Contract

## Test stance

Importer behavior should be tested over stable HTML fixtures and expected draft
outputs. Tests should prefer replayability and deterministic failure diagnosis.

## Required test families

### Discovery
- only allowlisted URLs are discovered
- only path-allowed URLs are discovered for the active profile
- index-page discovery preserves first-seen order after deduplication
- duplicate URLs collapse deterministically
- disallowed paths are excluded
- manifest output remains stable enough for snapshot comparison after normalizing
  volatile fields

### Fetch
- successful fetch writes raw and normalized artifacts
- disallowed HTTP hosts are rejected before network fetch
- bounded fetch policy is preserved in output metadata
- temporary HTTP failures may retry only within configured limits
- stronger `robots.txt` crawl-delay becomes the effective fetch pacing constraint
- browser fallback is used only when required
- non-200 or empty-content pages fail closed

### Extraction
- main content is preserved
- navigation and boilerplate are removed
- fragment ordering is stable
- reference links and related links are preserved

### Mapping
- required exported fields receive provenance
- low-confidence inferred fields are marked review-required
- unresolved fragments remain visible

### Validation
- missing required fields produce errors
- missing provenance produces errors
- low-confidence paths appear in reports
- invalid package cannot be marked approved

### Packaging
- generated package shape is stable
- package references source document ids
- validation summary is preserved in output

### Export
- export writes `topic-package.yaml`, `provenance.json`, and
  `validation-report.json`
- exported package remains stable enough for snapshot comparison after
  normalizing volatile fields
- `run` includes export materialization
- invalid validation reports block export
- provenance sidecar points back to the exact run artifacts used for export

## Golden-fixture expectations

Keep a small golden corpus of representative upstream pages:
- a normal chapter page
- a chapter page with richer section structure
- a page with unusual formatting or missing expected sections

For each golden fixture, preserve:
- raw HTML
- normalized text snapshot
- parsed fragments snapshot
- expected semantic draft
- expected validation report
- expected exported topic package snapshot

## Regression triggers

Re-run the importer test corpus when:
- parser selectors change
- normalization logic changes
- mapping heuristics change
- model-assisted prompts or policies change
- output contract changes
