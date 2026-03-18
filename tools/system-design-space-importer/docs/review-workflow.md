# Review Workflow

## Goal

The importer exists to reduce authoring effort, not to remove editorial control.

## Review stages

1. Import run completes.
2. Reviewer inspects `ValidationReport`.
3. Reviewer inspects `DraftTopicPackage`.
4. Reviewer checks provenance on low-confidence fields.
5. Reviewer edits, accepts, or rejects the draft.
6. Approved package becomes eligible for downstream materialization.

## Required reviewer checks

- title and topic boundaries are correct
- no important section is missing
- imported explanations did not lose core meaning
- inferred fields are reasonable and clearly marked
- concept/pattern/scenario separation is still valid
- learning-design suggestions did not leak into canonical truth

## Expected manual edits in v1

- normalize stable ids
- tighten descriptions
- add or fix `canonical_axes`
- add or refine `hint_ladders`
- remove weak inferred fields
- split one imported page into multiple content objects when needed

## Acceptance criteria

A draft package may be approved when:
- schema validation passes
- provenance is complete
- review-required fields were explicitly checked
- object boundaries are editorially sound
- unresolved warnings are understood and acceptable

## Rejection criteria

Reject or return for rework when:
- page structure was parsed incorrectly
- provenance is incomplete
- semantic mapping is overconfident
- draft package mixes canonical content with pedagogy
- imported output is too lossy to be trusted
