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

Default bounded HTTP policy:
- allowed hostnames: `system-design.space`, `www.system-design.space`
- timeout: `10s`
- retries: `1`
- rate limit: `250ms` between HTTP attempts
- local `file://` fixtures remain allowed for test and development workflows

Robots posture:
- fetch `robots.txt` for allowed HTTP seeds
- preserve parsed `crawl-delay` and disallow paths in manifest metadata
- treat `crawl-delay` as a lower-bound constraint on effective HTTP pacing
- local `file://` fixtures record `robots_policy = not_applicable_local_file`

Default discovery policy for `chapters_only`:
- seed may be either a direct chapter URL or a bounded index page
- only links under `/chapter/` are eligible discovery targets
- discovered URLs are deduplicated in first-seen order
- `max_pages` applies after filtering and deduplication

## Provenance requirements

Every exported draft package must preserve:
- `source_url`
- `fetched_at`
- `source_hash`
- `parser_version`
- source fragment references for each draft field
- run-level manifest linkage in the provenance sidecar

Recommended run-level metadata:
- run id
- seed URL set
- allowlist rules
- fetch mode used
- tool version
- timeout / retry / rate-limit policy

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
