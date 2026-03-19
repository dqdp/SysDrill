# Slice 008a: Frontend Navigation Invariants

## Status

- completed in current worktree

## Goal

Close a narrow UI-state bug in the thin frontend shell: once a manual session
has started, launcher-only controls must not mutate visible mode/intent state
for the active session.

## Why this exists

Browser verification found that the launch-profile picker remains interactive
during `session` and `review` phases. That allows the UI to show a different
profile label from the live session that was already started.

This is a contract-preserving bugfix, not a new product slice.

## In scope

- launcher/profile navigation invariants in the current `frontend/` shell
- frontend tests for the affected state transitions
- minimal UI changes required to preserve a truthful session display

## Out of scope

- backend contract changes
- resume/history navigation
- recommendation
- multi-page routing
- broader visual redesign

## Affected bounded contexts

- `Interaction Layer`
- `web_api / ui`

## Constraint

- launcher configuration and active session state must not diverge visibly
- profile selection remains editable only in launcher phase
- `Back to launcher` must restore editable launcher controls

## Approaches considered

### Option A: Disable launcher controls outside launcher

- keep a single `activeProfile`
- make profile radios launcher-only once a session has started

Trade-offs:
- minimal code
- preserves current shell simplicity
- enough for the thin demo path

### Option B: Split launcher profile from active session profile

- keep independent state for pending launcher config and live session config

Trade-offs:
- cleaner model
- more state and more test surface than this shell needs

Decision:
- choose Option A

## TDD plan

1. Add frontend tests that prove:
   - profile radios are enabled in launcher
   - they become disabled after session start
   - they remain disabled in review
   - `Back to launcher` makes them enabled again
2. Implement the minimal UI guard.
3. Run frontend verification.
4. Re-check the browser repro.

## Weak spots and assumption review

- hidden assumption: this shell does not need editable “next launch” controls
  while a session is active
- weak spot: if later slices add side-by-side “current session” and “next
  launch” planning, this invariant will need revisiting
- no contradiction found with the current v2.2 baseline because this change
  narrows UI behavior without altering domain contracts
