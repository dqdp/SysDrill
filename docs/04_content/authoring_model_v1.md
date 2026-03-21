# Authoring model v1

## Purpose

Define a practical content-production model for v1 that preserves the boundary between canonical content and learning design without forcing a heavy editorial workflow.

## Principle

v1 keeps `Content Kernel` and `Learning Design` separate at the level of:
- ownership
- schema
- runtime responsibility

v1 does **not** require those domains to be separated into fully independent editorial workflows.

## Recommended authoring unit

The recommended authoring unit for v1 is a **topic package**.
A topic package is a bundled authoring artifact that may contain multiple schema-distinct sections.

Bundled authoring is allowed because it reduces setup cost and helps bootstrap the first 50–100 high-quality learning units.

## Topic package structure

A v1 topic package may include three sections.

### A. Canonical content section
Owned by `Content Kernel`.

Typical fields:
- topic id
- concepts
- patterns
- explicit scenario-to-concept bindings where scenario outcomes need canonical
  concept follow-up targets
- canonical explanation
- why it matters
- trade-offs
- failure modes
- prerequisites
- related concepts
- baseline difficulty

### B. Canonical support section
Also owned by `Content Kernel`.

Typical fields:
- canonical hint ladder
- canonical follow-up candidates
- common misconceptions
- interview-relevant angles

### C. Learning-design bindings section
Owned by `Learning Design`.

Typical fields:
- allowed card types
- suggested exercise templates
- pedagogical goals
- recommended modes/intents
- delivery variants such as oral-capable prompts
- remediation suitability
- progressive coverage notes

## Required vs optional coverage

v1 uses **progressive coverage**, not exhaustive coverage.

Required expectation:
- each launch-worthy topic should have canonical content
- each launch-worthy topic should have at least one usable learning path into `Study` or `Practice`

Optional expectation:
- not every topic needs every card type
- not every topic needs an oral variant
- not every concept needs a direct scenario binding immediately
- not every topic needs a fully enriched remediation mapping at launch

## Template-assisted derivation

v1 prefers **template-assisted derivation** over fully manual handcrafted coverage.

Examples:
- a concept can seed a recall card from its canonical explanation and trade-offs
- a concept with competing design choices can seed a comparison card
- a concept with known failure modes can seed a failure drill
- a scenario can reuse a standard follow-up skeleton and then add scenario-specific overlays

Authors should curate and improve derived units, but the process should not require manual creation of every derivative from scratch.

## What bundled authoring does not permit

Bundled authoring does not mean:
- merging content truth and pedagogical ownership
- storing runtime orchestration rules in canonical content
- replacing schemas with arbitrary prose blobs
- demanding complete card-type coverage for every topic

## Minimal launch posture

A practical v1 launch posture can look like this:
- 8–10 core topics
- 50–100 high-quality learning units across those topics
- 3–5 mini-mock scenarios
- progressive enrichment after launch based on learner evidence

## Evolution path

As scale grows, the project may later split bundled topic packages into:
- separate canonical content files
- separate learning-design binding files
- stricter editorial review workflow
- more explicit provenance and versioning gates

That later split should be treated as an operational scaling step, not as a prerequisite for v1.
