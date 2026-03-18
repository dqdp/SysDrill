# Slice 006b: GitHub CI And Smoke Verification

## Status

- completed

## Goal

Add a repository-native verification foundation that runs in GitHub and covers
both fast static checks and the current end-to-end prototype seams with
deterministic smoke tests.

## Why this is on the critical path

The current backend and importer slices are locally testable, but the repository
does not yet have:
- a GitHub-native verification workflow
- a guaranteed clean-environment install path exercised on every change
- a coarse smoke path that proves the current prototype loop still works after
  integration changes

Without this slice, the project can continue to drift between:
- local developer environments
- undocumented verification expectations
- optimistic confidence from unit tests that do not exercise the current
  prototype seam from install to reviewed outcome

This slice is intentionally verification-first. It does not widen the domain
surface.

## In scope

- GitHub Actions workflows under `.github/workflows/`
- one blocking Python verification path for install, lint, format, and tests
- one smoke verification path for the importer fixture pipeline
- one smoke verification path for the backend manual reviewed loop
- a stable local command surface for the same checks
- narrow repository hygiene fixes required to make the verification path honest
  and green

## Out of scope

- real deployment or release automation
- frontend build or frontend test automation
- Dockerization
- recommendation or learner-state implementation
- scenario runtime expansion
- production observability or runtime metrics pipelines
- long-running browser or external-network integration tests

## Affected bounded contexts

- backend implementation infrastructure
- tooling verification around the importer
- web API verification for the current prototype path

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/05_ops/evaluation_quality_plan_v1.md`
- `README.md`
- `implementation/roadmap.md`
- `implementation/status.md`
- `tools/system-design-space-importer/docs/test-contract.md`

## Architectural approaches considered

### Option A: Minimal GitHub unit-check workflow only

- add one GitHub job
- install editable packages
- run lint, format-check, and unit tests

Trade-offs:
- fastest setup
- useful for baseline hygiene
- does not verify the current prototype seam end-to-end
- may miss regressions caused by wiring changes that unit tests do not expose

### Option B: GitHub unit-check workflow plus bounded local smoke paths

- add one blocking verification job
- add one smoke job over local fixtures and the current manual reviewed loop
- keep all smoke inputs local and deterministic
- reuse the same commands locally and in CI

Trade-offs:
- slightly wider than Option A
- still fast and deterministic
- validates the most important current integration seams without pretending to
  be full product coverage

Decision:
- choose Option B

### Option C: Full CI/CD with packaging and deployment

- add CI plus release artifacts and deployment hooks

Trade-offs:
- operationally attractive later
- premature for the current repository because no delivery target or release
  contract is defined yet

Rejected because:
- it would create the appearance of a deploy contract that the codebase and
  docs do not currently define

## Proposed implementation shape

- add a Python CI workflow under `.github/workflows/`
- add one local smoke script or make target for importer verification
- add one local smoke script or make target for backend manual reviewed loop
- keep smoke paths fixture-based and offline
- extend the root `Makefile` with explicit smoke commands if that produces the
  cleanest local/CI parity

## TDD plan

### Phase 1: verification contract tests first

Define the exact command surface before wiring GitHub.

Target contract:
- a clean environment can install backend and importer editable packages
- lint and format-check can run from the repo root
- backend unit tests can run from the repo root
- importer unit tests can run from the repo root
- the smoke commands are deterministic and non-interactive

### Phase 2: importer smoke path

Add a bounded smoke command that proves the importer pipeline still materializes
an export bundle from fixtures.

Smoke contract:
- run `discover -> fetch -> extract -> map -> validate -> package -> export`
  against fixture input only
- verify the expected export tree is created
- fail closed if export output is missing or validation blocks export

### Phase 3: backend smoke path

Add a bounded smoke command that proves the current backend prototype seam still
works from content load to reviewed outcome.

Smoke contract:
- load the fixture export root
- start a manual session over one materialized unit
- submit one answer
- attach evaluation
- retrieve review
- fail closed if any state transition or required response shape is broken

### Phase 4: GitHub workflow wiring

Add the GitHub workflow only after the local command surface is explicit.

Workflow contract:
- run on `push` and `pull_request`
- use `Python 3.12`
- install backend and importer editable packages from scratch
- run lint, format-check, unit tests, and smoke verification
- publish a failing status if any blocking verification step fails

## Test contract

- GitHub workflow succeeds on a clean checkout with no pre-existing `.venv`
- `ruff check` passes
- `ruff format --check` passes
- backend unit tests pass
- importer unit tests pass
- importer smoke verification passes using only local fixtures
- backend smoke verification passes using only local fixtures
- smoke verification does not require external network access
- smoke verification does not require a manually started server process

## Acceptance criteria

- repository contains a documented GitHub verification workflow
- local and CI verification use the same bounded command surface
- current prototype seam is covered by at least one coarse smoke path
- no new product-domain scope is introduced
- verification remains deterministic and fast enough for normal PR use

## Weak spots and assumption review

- hidden assumption: `Python 3.12` remains the CI baseline even if some local
  contributors run a newer interpreter; this should match the declared project
  baseline and avoid accidental compatibility drift
- hidden assumption: current smoke coverage should target only the implemented
  prototype seam, not the full documentation surface
- weak spot: current `ruff` violations mean the repository is not yet honestly
  CI-ready; this slice must either fix them or explicitly narrow the blocking
  checks, and the first option is strongly preferred
- weak spot: if smoke verification starts a real HTTP server or reaches the
  external network, the suite will become slower and flakier than necessary
- weak spot: calling this `CI/CD` would overstate the current scope; this slice
  is CI plus smoke verification, not deployment automation
- no contradiction found with the v2.2 documentation baseline because this
  slice hardens verification rather than revising architecture

## ADR check

No ADR is required if this slice:
- keeps verification concerns outside runtime/recommendation ownership changes
- does not revise bounded contexts or contracts
- does not introduce a new deployment model

## Verification

- run the new local verification commands in a clean environment
- run the GitHub workflow on a branch or PR
- confirm local and CI results match for the bounded checks

## Definition of done

- explicit slice-level TDD contract exists and is reviewed
- GitHub workflow files exist and are valid
- root verification commands are documented and green
- importer and backend smoke paths both exist and pass
- `implementation/roadmap.md` and `implementation/status.md` reflect the new
  execution order

## Review result

- recommended next step after this plan is implementation of the verification
  slice itself, not expansion of product-domain scope
- no conflicts found with `AGENTS.md`, the current ADR set, or the v2.2
  documentation baseline

## Outcome

- the repository now includes a GitHub Actions workflow for Python verification
  and bounded smoke checks
- the root `Makefile` now exposes explicit local commands for bootstrap,
  verification, and smoke checks
- importer and backend smoke tests now cover the current fixture-based
  prototype seam
- the Python verification surface is green locally via `make ci-python`
