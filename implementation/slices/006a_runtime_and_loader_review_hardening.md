# Slice 006a: Runtime And Loader Review Hardening

## Status

- completed

## Goal

Close four narrow correctness gaps discovered during review of the current
manual runtime and content bootstrap path without widening the architecture
beyond the current prototype baseline.

## Why this slice exists

Review of the current worktree found four concrete defects:
- concurrent answer submission can append duplicate runtime events and overwrite
  the latest evaluation hand-off
- the configured content export root may still be a symlink even though bundle
  traversal otherwise rejects symlinked paths
- topic summary projection can raise incidental `500` errors on malformed nested
  bundle sections such as `validation_summary: null`
- health-only bootstrap can fail on an irrelevant malformed draft-loading flag

These are contract-hardening defects, not a reason to redesign the runtime,
loader, or deployment model.

## In scope

- process-local synchronization for in-memory runtime state transitions
- fail-closed rejection of symlinked configured export roots
- defensive summary projection for nullable nested topic-package sections
- health-only bootstrap semantics when no content root is configured
- targeted regression tests for each defect

## Out of scope

- database persistence
- multi-process runtime coordination
- content schema redesign
- automatic content snapshot discovery
- recommendation or learner-state changes
- evaluation-model redesign

## Affected bounded contexts

- `Session Runtime`
- `Content Kernel`
- `web_api / ui`

## Source-of-truth references

- `docs/00_change_protocol.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `implementation/slices/003a_content_catalog_hardening.md`
- `implementation/slices/005a_bootstrap_and_runtime_contract_hardening.md`
- `implementation/slices/006_rule_first_evaluation_loop.md`

## Architectural approaches considered

### Option A: Minimal hardening on existing seams

- add process-local locking inside `SessionRuntime`
- reject a symlinked configured export root before path resolution
- normalize nullable nested mappings in content summary projection
- parse draft-loading env only when content loading is actually enabled

Trade-offs:
- smallest contract-preserving patch
- keeps current prototype posture intact
- does not solve cross-process coordination, only in-process correctness

### Option B: Broader contract tightening

- introduce per-session lock management or a persistence-backed runtime
- perform deeper nested schema validation during bundle load
- redesign bootstrap config parsing into a more formal settings object

Trade-offs:
- cleaner long-term shape
- materially wider scope than the reviewed defects
- higher risk of accidental architecture churn

Decision:
- choose Option A

## Test contract

- concurrent submission for one session yields at most one successful stable
  answer boundary and exactly one `answer_submitted` event
- concurrent evaluation attachment for one session yields at most one reviewed
  outcome and does not duplicate `evaluation_attached` / `review_presented`
- a symlinked configured export root is rejected with explicit `BundleLoadError`
- `/content/topics` tolerates nullable nested sections that are not guaranteed by
  the loader contract and falls back instead of raising incidental `500`
- module-level health-only bootstrap remains available when no content root is
  configured even if `SYSDRILL_ALLOW_DRAFT_BUNDLES` is malformed
- malformed draft-loading flags still fail closed when content loading is
  explicitly enabled

## Acceptance criteria

- in-memory runtime state transitions are serialized within one process
- loader traversal rejects a symlinked configured export root consistently with
  the existing no-symlink posture
- content summary projection is defensive against nullable nested mappings
- health-only startup behavior is preserved when content loading is disabled
- no bounded-context ownership or baseline v2.2 decisions are changed

## Weak spots and assumption review

- assumption: process-local serialization is sufficient for the current
  prototype because runtime state is already process-local and undocumented for
  multi-process sharing
- weak spot: a single runtime lock may reduce throughput, but that trade-off is
  acceptable for the current bounded prototype and is safer than partial
  locking
- assumption: nested bundle sections beyond required files are not fully schema
  validated at load time, so projection code must fail safely
- assumption: `create_app()` without content config must remain legal for
  health-only startup; this preserves an existing documented contract
- no contradiction found with the v2.2 baseline or current ADR-level decisions
- no ADR is required because this slice hardens existing contracts instead of
  revising architecture

## Verification

- targeted backend unit/API tests for runtime concurrency, loader root checks,
  summary projection, and bootstrap env behavior
- `PYTHONPATH=backend/src python3 -m pytest -q backend/tests`

## Outcome

- `SessionRuntime` now serializes process-local state transitions so one session
  cannot accept duplicate answer submission or duplicate evaluation attachment
  within the same process
- content loading now rejects a symlinked configured export root consistently
  with the existing strict no-symlink posture
- topic summary projection now tolerates nullable nested sections and falls back
  safely instead of surfacing incidental `500` errors
- health-only bootstrap now ignores malformed draft-loading flags when content
  loading is not enabled, while preserving fail-closed behavior for configured
  content startup
