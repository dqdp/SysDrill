# Test Contract

## Test stance

Importer behavior should be tested over stable HTML fixtures and expected draft
outputs. Tests should prefer replayability and deterministic failure diagnosis.

## Required test families

### Discovery
- only allowlisted URLs are discovered
- duplicate URLs collapse deterministically
- disallowed paths are excluded

### Fetch
- successful fetch writes raw and normalized artifacts
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

## Regression triggers

Re-run the importer test corpus when:
- parser selectors change
- normalization logic changes
- mapping heuristics change
- model-assisted prompts or policies change
- output contract changes
