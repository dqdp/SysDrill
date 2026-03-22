# Slice 018b: Frontend Shell Decomposition

## Status

- completed

## Goal

Reduce the structural risk in [App.tsx](/Users/alex/SysDrill/frontend/src/App.tsx)
without changing frontend behavior, backend APIs, or the current bounded shell
scope.

Expected outcome:
- launcher, session, and review rendering become separate components
- restore/recommendation orchestration moves behind a dedicated hook or narrow
  controller seam
- `App.tsx` becomes a composition root instead of a monolithic state machine
- existing user-visible behavior and backend call ordering remain unchanged

## Affected bounded contexts

- `web_api / ui`

## Non-goals

- no backend changes
- no router introduction
- no new state-management library
- no visual redesign
- no durable persistence changes
- no product-surface expansion
- no new mode or scenario behavior

## Constraints

- frontend remains a thin backend-driven shell
- browser-local resume and recommendation persistence remain temporary
  scaffolding
- decomposition must preserve existing launcher/session/review semantics
- test contract must be aligned before code
- no unrelated cleanup or stylistic churn

## Hidden assumptions to lock before code

- the current main complexity problem is orchestration density, not rendering
  complexity alone
- decomposition is valuable even if it yields little immediate user-visible
  value, because future frontend slices would otherwise keep amplifying risk in
  one file
- behavior preservation is more important than achieving an ideal component
  hierarchy in one pass

## Why this slice exists

After `018a`:
- frontend docs are truthful again
- mock-family coverage proves the shell is not implicitly specialized to one
  scenario family
- frontend verification is green

What remains risky:
- [App.tsx](/Users/alex/SysDrill/frontend/src/App.tsx) is already large enough
  to mix rendering, API orchestration, restore logic, retry logic, and
  launcher/session/review transitions in one file
- the next frontend change would likely increase incidental coupling unless the
  shell is split along responsibility boundaries first

## Architectural approaches considered

### Option A: Shallow decomposition

Shape:
- extract presentational shells for launcher, session, and review
- extract one orchestration hook for restore/recommendation/session transitions
- keep the current state model mostly intact

Pros:
- smallest safe maintainability step
- preserves behavior with lower review risk
- avoids introducing a new architectural abstraction prematurely

Cons:
- internal state model may still look dense after extraction
- some helper functions may remain transitional rather than ideal

### Option B: Deep decomposition with explicit reducer/page model

Shape:
- redesign `App.tsx` around a reducer or explicit page-state machine
- extract components and move orchestration into reducer-driven actions

Pros:
- potentially cleaner long-term internal model
- could further reduce implicit coupling

Cons:
- much higher behavior-regression risk
- larger review surface
- effectively an architecture change inside the frontend shell

## Recommendation

Choose Option A.

Reasoning:
- the current problem is maintainability pressure, not a proven need for a new
  internal frontend architecture
- a narrow extraction pass can materially reduce complexity while preserving the
  thin-shell posture
- deeper normalization should be reconsidered only if shallow decomposition
  still leaves a clear operational problem

## Proposed decomposition boundaries

### 0. `ProfileSelector`

Responsibility:
- render launch-profile selection consistently across launcher/session/review
- stay visible but disabled outside launcher phase

Must not own:
- launcher data loading
- session/review transitions

### 1. `LauncherShell`

Responsibility:
- render recommendation state
- render learner summary state
- render manual launch options
- expose callbacks for start/reset/retry actions

Must not own:
- backend fetching logic
- restore/session orchestration

### 2. `SessionShell`

Responsibility:
- render the active prompt
- render answer textarea and submission state
- show in-session errors

Must not own:
- evaluation/review fetching policy
- launcher data loading

### 3. `ReviewShell`

Responsibility:
- render evaluation/review payload
- expose `Back to launcher`

Must not own:
- restore logic
- recommendation fetching logic

### 4. `useRuntimeShell` or equivalent orchestration seam

Responsibility:
- restore saved session
- load recommendation/manual options/learner summary
- coordinate start/submit/reset/retry flows
- keep backend call ordering and recovery policy in one place

Must not:
- introduce a second client-side runtime model
- become a generic framework abstraction

## Test contract

Tests should be updated before code changes.

### 1. Behavior-preservation tests

Existing integration-style tests in
[App.test.tsx](/Users/alex/SysDrill/frontend/src/App.test.tsx) should keep
passing with minimal expectation churn.

Required preserved flows:
- recommendation-driven launch to review
- manual bounded mock flow
- restore of awaiting-answer session
- restore/review recovery paths
- stale recommendation recovery
- idempotent recommendation start replay handling

### 2. New decomposition-local tests

Add or update tests so that:
- launcher rendering can be exercised without booting the entire app flow
- review rendering can be exercised without relying on unrelated launcher
  behavior
- family-agnostic mock content still renders via the same shells

These tests may live in:
- `frontend/src/App.test.tsx`
- or new focused tests next to extracted components/hooks, if that reduces
  duplication without changing coverage posture

### 3. Verification

Then:
- `make verify-frontend` passes

## Acceptance criteria

- `App.tsx` is materially smaller and acts primarily as a composition root
- launcher/session/review responsibilities are separated into dedicated shells
- restore/recommendation/session orchestration is isolated behind a narrow hook
  or controller seam
- frontend behavior is preserved
- `make verify-frontend` is green

## Weak spots review

- shallow extraction can accidentally create prop-drilling noise; if that
  happens, prefer a small local view-model shape over broad context providers
- splitting helpers without a clear responsibility boundary would create file
  churn without reducing risk; each extracted unit must own a coherent slice of
  behavior
- this slice should not treat “smaller files” as success by itself; preserved
  call ordering and recovery semantics are the real acceptance gate

## Source-of-truth review

- `docs/00_change_protocol.md`: implementation-only frontend-shell change; ADR
  not required
- `docs/03_architecture/session_runtime_state_machine_v1.md`: preserved
- `docs/03_architecture/recommendation_engine_surface.md`: preserved
- `docs/00_implementation_baseline_v2.2.md`: preserved

## Change protocol notes

Expected affected bounded contexts:
- `web_api / ui`

Expected source-of-truth files updated:
- none
- frontend-local docs may remain unchanged if slice scope stays purely
  structural

ADR required:
- no

Schema/example files updated:
- none

Invariants intentionally preserved:
- frontend remains a thin backend-driven shell
- browser-local resume remains temporary scaffolding
- top-level modes remain unchanged
- no new frontend architecture contract is introduced

Baseline:
- this slice should preserve the v2.2 implementation baseline
