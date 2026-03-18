# ADR-008: Bundled authoring with schema-distinct content and learning design in v1

Date: 2026-03-18
Status: Accepted

## Context

The system already treats `Content Kernel` and `Learning Design` as separate ownership domains.
That separation is important for long-term quality, explainability, and runtime clarity.

However, a fully separated editorial workflow in v1 would impose too much authoring overhead:
- too many artifacts per concept or scenario
- too much manual coverage work before launch
- too much coordination cost for early content production

The project needs a practical way to produce an initial body of high-quality material quickly without collapsing the conceptual boundary between content truth and pedagogical transformation.

## Decision

For v1, the project will keep **strict conceptual and schema separation** between:
- canonical content entities owned by `Content Kernel`
- pedagogical bindings and exercise templates owned by `Learning Design`

At the same time, v1 **allows bundled topic authoring** as an operational shortcut.
A single topic package may include both canonical content sections and learning-design sections, provided they remain schema-distinct and ownership-distinct.

The project also accepts **template-assisted derivation** of learning units in v1. Authors may generate or curate learning units from reusable templates rather than handcrafting full coverage for every concept.

Coverage is **progressive, not exhaustive**. Not every concept must map to every supported exercise type in the first release.

## Consequences

### Positive
- preserves architectural integrity without creating an editorial bureaucracy
- increases velocity for the initial content bootstrap
- keeps room for later separation of workflows if scale demands it
- encourages reusable exercise patterns instead of handcrafted sprawl

### Negative
- bundled topic packages require discipline to avoid turning into unstructured blobs
- the system must clearly mark required vs optional derived learning artifacts
- future workflow separation may require package refactoring

## Guardrails

Bundled authoring in v1 does **not** mean:
- collapsing content and learning design ownership
- mixing runtime behavior rules into canonical content truth
- requiring every topic to contain every exercise type
- storing arbitrary prompt soup in place of schema-backed artifacts

## Follow-up

The package should explicitly document:
- the v1 authoring model
- minimal required vs optional fields
- progressive coverage expectations
- template-assisted derivation rules
