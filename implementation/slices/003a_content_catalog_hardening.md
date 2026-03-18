# Slice 003a: Content Catalog Hardening

## Status

- completed

## Goal

Harden bundle loading and content-catalog startup behavior so misconfigured or
malformed content roots fail closed with explicit domain errors.

## Why this is on the critical path

Slices 002 and 003 established the first runtime-facing content hand-off.

The current happy path works, but review found three concrete correctness gaps:
- configured roots that yield no bundles are accepted silently
- symlinked directories can route loading outside the configured root
- wrong-shaped bundle payloads can escape as runtime `AttributeError` instead of
  explicit `BundleLoadError`

These are narrow defects in the existing contract, not reasons to broaden the
architecture or loader surface.

## In scope

- fail-closed rejection when an explicitly configured export root yields no
  topic bundles
- fail-closed rejection of symlinked source/topic directories during export-root
  traversal
- explicit shape validation for required bundle payload files before field access
- targeted backend tests for the above scenarios

## Out of scope

- auto-discovery of the "latest" exporter output
- support for passing per-source directories as `content_export_root`
- schema-level validation beyond the existing required-file and
  `validation-report.schema_valid` checks
- API contract expansion
- changes to bounded-context ownership

## Affected bounded contexts

- `Content Kernel`
- implementation-side backend infrastructure around content loading
- `web_api / ui`

## Source-of-truth references

- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/04_content/content_schema.md`
- `docs/04_content/authoring_model_v1.md`
- `tools/system-design-space-importer/docs/contracts.md`
- `implementation/slices/002_content_bundle_reader.md`
- `implementation/slices/003_content_catalog_api_surface.md`

## Architectural options considered

### Option A: Strict hardening of the existing loader contract

- require a top-level export root that materializes at least one bundle
- reject symlinked traversal entirely
- require required bundle files to deserialize as mappings/objects

Trade-offs:
- preserves the current explicit/fail-closed posture
- keeps implementation small and deterministic
- intentionally rejects some potentially convenient deployment shapes

### Option B: Broaden the loader contract

- accept either top-level export roots or per-source roots
- allow symlinks if their resolved path stays under the configured root
- normalize malformed payloads more permissively

Trade-offs:
- more flexible for operations and local workflows
- increases complexity and ambiguity in the runtime contract
- conflicts with the current goal of explicit, narrow content startup behavior

Decision:
- choose Option A for this slice

## Test contract

- reader rejects an explicitly configured export root when it yields zero topic
  bundles
- app startup fails closed when a configured export root yields zero topic
  bundles
- reader rejects symlinked source directories
- reader rejects symlinked topic directories
- reader rejects `topic-package.yaml` when it deserializes to a non-mapping
- reader rejects `provenance.json` when it deserializes to a non-object
- reader rejects `validation-report.json` when it deserializes to a non-object
- malformed bundle payloads raise explicit `BundleLoadError`, not incidental
  runtime exceptions
- existing valid bundle fixtures still load successfully
- existing read-only topic endpoints remain unchanged for valid configurations

## Acceptance criteria

- explicitly configured invalid content roots fail closed during startup
- loader traversal remains inside the configured export root
- malformed bundle payloads fail with explicit domain errors
- no new loader modes or API surface area are introduced
- slices 002 and 003 remain narrow and deterministic

## Weak spots and assumption review

- assumption: `create_app()` without `content_export_root` must remain valid for
  health-only startup; this slice does not change that behavior
- assumption: per-source export directories are not a supported runtime input;
  this is preserved intentionally rather than normalized
- weak spot: symlink rejection is stricter than a resolved-under-root policy, but
  it is the smallest deterministic policy that preserves the current invariant
- no contradiction found with v2.2 baseline or any frozen ADR-level decision
- no ADR is required because this hardening preserves existing contracts and
  bounded-context ownership

## Verification

- targeted unit tests for `content_bundle_reader`
- targeted API tests for startup failure cases
- `make verify-python`

## Definition of done

- new regression tests exist for the three reviewed defects
- loader implementation passes the new tests with minimal contract-preserving
  changes
- implementation status docs are synced
- the v2.2 implementation baseline remains preserved

## Outcome

- invalid configured content roots now fail closed when no topic bundles are
  materialized
- symlinked source/topic directories are rejected during export-root traversal
- malformed required bundle payloads now raise explicit `BundleLoadError`
  messages instead of incidental runtime exceptions
