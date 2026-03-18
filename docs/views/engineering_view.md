# Engineering View

## Main engineering objective

Собрать систему из нескольких простых и чётких контуров,
а не из одного большого prompt stack.

## Implementation priorities

1. content schema and authoring pipeline
2. session orchestration
3. interaction event log
4. evaluation engine
5. learner profile projection
6. recommendation engine
7. UI polish
8. voice later

## Preferred design bias

- explicit schemas over implicit prompt conventions
- append-only semantic events over mutable “latest state only”
- rationale-bearing recommendation decisions
- hybrid evaluation over pure freeform LLM judgment
- text-first validation before voice complexity
- three runtime modes plus session intent over proliferating pseudo-modes
- Python-first backend and tooling over forcing a single language across the repo
- separate TypeScript frontend when the UI surface justifies it

## Where complexity should be allowed

- content modeling
- scoring contracts
- learner profile projection
- recommendation rationale

## Where complexity should be resisted

- premature microservices
- opaque AI-only orchestration
- storing everything as raw chat text
- UI-owned business logic
- turning remediation into a fourth runtime family

## Telemetry constraint

В v1 engineering path должен собирать semantic learning events с coarse timing,
а не превращать learner evidence layer в raw UI exhaust stream. Более детальная
телеметрия может жить отдельно как product analytics or infra diagnostics.


## Authoring and content production stance

Engineering should assume that v1 content may arrive as bundled topic packages rather than as fully separated editorial artifacts.

The implementation must therefore support:
- schema-distinct sections inside bundled authoring packages
- optional learning-design derivatives
- template-assisted generation or curation workflows
- progressive enrichment without requiring exhaustive content coverage from day one

## Repository tooling posture

- use a root Python `.venv` for backend and Python-based tools
- keep Python packages logically separate even when they share one environment
- treat `ruff` as part of the default verification loop alongside tests
- keep frontend package management independent from the Python environment
