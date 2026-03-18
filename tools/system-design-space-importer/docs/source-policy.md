# Source Policy

## Upstream source

The initial upstream source for this tool is:
- `https://system-design.space/`

This source reference is intentionally local to the importer tool and is not a
product-level dependency contract.

## Import boundary

The importer should treat the upstream site as a source of raw material, not as
runtime source of truth.

Allowed import targets:
- chapter pages
- reference pages directly linked from chapter content, if explicitly enabled

Disallowed by default:
- account-only surfaces
- user-specific progress surfaces
- analytics or settings pages
- externally linked content as first-class imported content

## Compliance posture

Before widening crawl scope, verify:
- robots posture
- crawl rate limits
- copyright and licensing assumptions
- whether full-content storage is operationally acceptable

The importer must support bounded crawl scope and polite rate limiting.

## Provenance requirements

Every exported draft package must preserve:
- `source_url`
- `fetched_at`
- `source_hash`
- `parser_version`
- source fragment references for each draft field

Recommended run-level metadata:
- run id
- seed URL set
- allowlist rules
- fetch mode used
- tool version

## Refresh policy

Re-import is allowed when:
- source content changes
- parser logic changes
- mapping logic changes
- editorial refresh is requested

Recommended behavior:
- keep old run artifacts
- generate a new draft package
- compare by source hash and field-level diffs

## Fail-closed rules

Do not publish a draft package as approved if:
- main content extraction failed
- required provenance is missing
- title or primary summary is empty
- validation reports unresolved schema errors
