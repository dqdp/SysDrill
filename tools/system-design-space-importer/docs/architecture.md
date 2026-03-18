# Importer Architecture

## Purpose

`system-design-space-importer` is an operational ingestion tool.
It converts upstream web content into local, reviewable, schema-aligned drafts.

It does not redefine the main project architecture and does not become a
runtime dependency of learner-facing product flows.

## Main design constraints

- upstream source detail must remain local to this tool
- imported content must preserve provenance
- extraction must be replayable
- low-confidence inference must be review-gated
- tool output must be file-based and diffable
- importer failures must fail closed

## Pipeline stages

### 1. Discovery

Input:
- seed URLs
- allowlist rules
- import profile

Output:
- bounded list of candidate source URLs

### 2. Fetch

Input:
- candidate source URLs

Behavior:
- use plain HTTP by default
- use browser fallback only when page content is not materially available
  in fetched HTML

Output:
- `SourceDocument`
- raw HTML snapshot
- normalized text snapshot

### 3. Extraction

Input:
- fetched source document

Behavior:
- isolate main content
- remove navigation, chrome, and unrelated boilerplate
- extract stable content fragments and links

Output:
- `ParsedSourceFragment[]`

### 4. Mapping

Input:
- parsed fragments

Behavior:
- build a semantic draft over explicit contracts
- mark inferred fields and low-confidence fields
- do not silently promote weak inference to canonical truth

Output:
- `SemanticDraft`

### 5. Validation

Input:
- semantic draft

Behavior:
- check required fields
- check provenance completeness
- check id stability rules
- check review-required flags

Output:
- `ValidationReport`

### 6. Packaging

Input:
- validated semantic draft

Behavior:
- produce a reviewable topic package
- preserve a separate provenance trail

Output:
- `DraftTopicPackage`

## Runtime boundaries

The importer may later feed a separate materialization step, but it must not:
- write directly into runtime session/evaluation/recommendation stores
- collapse Content Kernel and Learning Design ownership
- bypass editorial review for inferred fields

## Recommended implementation bias

- deterministic extraction first
- bounded model assistance second
- human review before acceptance
- append-only run artifacts

## Suggested package shape

```text
tools/system-design-space-importer/
  README.md
  docs/
  examples/
  src/
  tests/
```
