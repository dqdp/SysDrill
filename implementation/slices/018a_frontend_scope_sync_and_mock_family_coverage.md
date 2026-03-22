# Slice 018a: Frontend Scope Sync And Mock Family Coverage

## Status

- completed

## Goal

Close the immediate frontend hardening gap after completed `017` so that:
- frontend docs truthfully describe the current shell scope, including bounded
  mock-readiness support
- frontend test coverage proves that the current mock UI path is family-agnostic
  for at least the existing `URL Shortener` and `Rate Limiter` families
- the current shell remains thin and backend-driven without reopening routing,
  state-library, or visual redesign work

## Affected bounded contexts

- `web_api / ui`
- documentation for the frontend shell boundary
- narrow consumption of existing `session_runtime` and `recommendation_engine`
  surfaces

## Non-goals

- no backend API changes
- no new top-level frontend route model
- no visual redesign
- no durable multi-device persistence
- no new product surface beyond what the backend already exposes
- no decomposition of `App.tsx` in this slice

## Constraints

- frontend remains a thin orchestration shell over backend truth
- mock support remains bounded to the existing `MockInterview / ReadinessCheck`
  runtime contract
- family-agnostic behavior must be proven through existing shell seams, not by
  introducing family-specific UI branching
- browser-local resume and recommendation persistence remain temporary
  scaffolding, not a durable contract

## Hidden assumptions to lock before code

- current mock launcher/session/review UI should not mention `URL Shortener`
  specifically unless the backend-provided prompt/title does so
- family validation at the frontend layer is sufficient if the same shell can
  launch, restore, and review two different scenario families without special
  casing
- README drift is now large enough to justify a dedicated docs-sync slice
  rather than waiting for a broader frontend refactor

## Architectural approaches considered

### Option A: Docs sync plus test coverage only

Shape:
- update `frontend/README.md`
- extend `frontend/src/App.test.tsx` to cover a second mock family
- keep production code untouched unless tests expose an actual family-specific
  UI bug

Pros:
- smallest possible scope
- preserves the thin-shell posture
- gives a clean signal on whether the current UI already generalizes

Cons:
- does not reduce `App.tsx` complexity
- may reveal a real UI coupling that then needs a tiny code fix anyway

### Option B: Combine docs sync, tests, and shell decomposition

Shape:
- update docs
- add family-agnostic mock tests
- start splitting `App.tsx` into launcher/session/review pieces

Pros:
- addresses both correctness and maintainability
- avoids a follow-up planning pass

Cons:
- mixes documentation/coverage hardening with structural refactor
- weakens scope discipline
- raises review cost for a slice whose primary goal is truthfulness and
  portability

## Recommendation

Choose Option A.

Reasoning:
- the immediate gap is contract drift between docs/tests and current behavior
- `App.tsx` decomposition is valuable, but it is a separate maintainability
  slice and should not be bundled into a scope-sync pass
- if family-agnostic mock coverage reveals a real coupling bug, fix only that
  bug here; otherwise keep production code unchanged

## Test contract

### 1. README scope sync

Given:
- the frontend shell as implemented today

Then:
- `frontend/README.md` states that bounded mock/readiness flows are supported
- it distinguishes that support from richer dashboards or durable resume
- it still describes the shell as backend-driven and browser-local for resume

### 2. Manual mock launcher remains family-agnostic

Given:
- manual launch options for `MockInterview / ReadinessCheck`
- one launch option for `URL Shortener`
- one launch option for `Rate Limiter`

Then:
- the same mock launcher UI can render and start both without family-specific
  code branches
- the session prompt and review content come from backend payloads, not from
  hardcoded frontend family assumptions

### 3. Recommendation/restore path stays generic

Given:
- a recommendation-backed or restored mock session from a non-`URL Shortener`
  family

Then:
- the existing shell routes to session/review correctly
- no stale family-specific labels or assumptions leak into the UI

### 4. Verification

Then:
- `make verify-frontend` passes

## Acceptance criteria

- frontend docs truthfully describe the current bounded mock scope
- frontend tests prove that the shell is not implicitly specialized to only one
  scenario family
- no backend changes are required
- no new frontend architecture is introduced
- `make verify-frontend` is green

## Weak spots review

- if tests reveal that the shell is coupled to `URL Shortener` wording in more
  places than expected, this slice should fix only the narrow rendering bug,
  not redesign the whole mock UI
- docs can become stale again quickly unless later frontend slices explicitly
  treat README sync as part of their acceptance
- this slice does not reduce `App.tsx` complexity; it only makes that risk
  more visible and better covered

## Source-of-truth review

- `docs/00_change_protocol.md`: implementation-only/frontend-shell change;
  ADR not required
- `docs/03_architecture/session_runtime_state_machine_v1.md`: preserved
- `docs/03_architecture/recommendation_engine_surface.md`: preserved
- `docs/00_implementation_baseline_v2.2.md`: preserved

## Change protocol notes

Expected affected bounded contexts:
- `web_api / ui`

Expected source-of-truth files updated:
- none
- frontend-local docs: `frontend/README.md`

ADR required:
- no

Schema/example files updated:
- none

Invariants intentionally preserved:
- frontend remains a thin backend-driven shell
- browser-local resume remains temporary scaffolding
- top-level modes remain unchanged
- no family-specific frontend orchestration layer is introduced

Baseline:
- this slice should preserve the v2.2 implementation baseline
