# Slice 005a: Bootstrap And Runtime Contract Hardening

## Status

- completed

## Goal

Close four narrow correctness gaps in the current backend bootstrap and manual
runtime path without widening the architecture beyond the current prototype
slices.

## Why this slice exists

Review of slices `003a`, `004`, and `005` found four concrete defects:
- the module-level ASGI app boots in health-only mode, so content/runtime
  endpoints are unreachable through the default import path
- runtime POST endpoints accept raw `dict` bodies and can surface incidental
  `500` errors for malformed requests
- required bundle sidecar files may still be symlinked outside the configured
  export snapshot
- runtime answer submission does not enforce unit `completion_rules`

These are contract-hardening defects, not a request to redesign bootstrap,
runtime, or content ownership.

## In scope

- explicit configured ASGI bootstrap for content/runtime surfaces
- typed request validation for runtime POST endpoints
- fail-closed rejection of symlinked required bundle files
- runtime enforcement of `completion_rules.submission_kind`
- targeted regression tests for each defect

## Out of scope

- exporter contract changes
- auto-discovery of a latest content snapshot
- database persistence
- recommendation logic
- evaluation execution
- follow-up, hint, or reveal endpoint expansion

## Affected bounded contexts

- `Content Kernel`
- `Session Runtime`
- `web_api / ui`

## Source-of-truth references

- `docs/00_change_protocol.md`
- `docs/02_domain/hand_off_contracts.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `implementation/slices/003a_content_catalog_hardening.md`
- `implementation/slices/005_session_runtime_and_event_log_bootstrap.md`

## Architectural approaches considered

### Option A: Minimal hardening on the current seams

- keep `create_app(...)` as the explicit factory
- add a thin configured ASGI bootstrap adapter
- validate request bodies with typed DTOs
- harden file/path checks and runtime submission checks locally

Trade-offs:
- smallest contract-preserving patch
- keeps bootstrap/config concerns out of runtime logic
- introduces one more small adapter module

### Option B: Fold deployment bootstrap into `create_app()` defaults

- teach `create_app()` to discover or read runtime configuration implicitly
- keep a single module-level `app`

Trade-offs:
- fewer files
- weaker explicitness around startup configuration
- higher risk of reintroducing hidden environment coupling

Decision:
- choose Option A

## Test contract

- configured ASGI bootstrap exposes non-empty content/runtime surfaces when
  explicit content config is present
- `create_app()` without content config remains valid for health-only startup
- malformed runtime POST payloads fail with `422`, not incidental `500`
- symlinked required bundle files raise explicit `BundleLoadError`
- invalid `submission_kind` is rejected before state transition
- rejected submissions do not emit `answer_submitted`

## Acceptance criteria

- module-level configured bootstrap no longer serves empty content/runtime
  surfaces by default
- POST body validation is explicit and deterministic
- loader traversal stays within the configured export snapshot for required
  sidecars as well as directories
- runtime enforces the selected unit's completion boundary
- no bounded-context ownership changes are introduced

## Weak spots and assumption review

- assumption: `create_app()` without content config must remain legal for
  health-only startup; this slice preserves that path
- assumption: explicit startup config is acceptable for the prototype bootstrap
  and preferable to snapshot auto-discovery
- weak spot: adding request DTOs narrows the HTTP contract; this is intended
  because the current raw-`dict` behavior is undefined and unsafe
- no ADR is required because the slice hardens existing contracts instead of
  revising architecture or invariants
