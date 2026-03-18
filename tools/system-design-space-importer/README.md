# System Design Space Importer

This tool imports source material from `https://system-design.space/` into
reviewable draft artifacts for the System Design Trainer knowledge base.

The importer is intentionally isolated from the main product architecture.
The product depends on normalized knowledge artifacts, not on the upstream site.

## Runtime requirement

This tool requires Python `>=3.12`.

## Scope

The importer is responsible for:
- discovering allowed source pages
- fetching and normalizing source documents
- extracting structured page fragments
- mapping fragments into reviewable draft topic packages
- validating draft outputs before editorial review
- materializing reviewable export bundles for downstream consumption

The importer is not responsible for:
- writing directly into runtime databases
- changing product-level architecture contracts
- bypassing human review for canonical content
- generating evaluation bindings as authoritative output

## Output posture

The importer writes file-based draft artifacts only:
- `SourceDocument`
- `ParsedSourceFragment`
- `SemanticDraft`
- `DraftTopicPackage`
- `ValidationReport`
- exported `topic-package.yaml` bundles with provenance sidecars

These artifacts are reviewed and approved before any downstream materialization
into `Content Kernel` or `Learning Design` storage.

## Pipeline

1. `discover`
2. `fetch`
3. `extract`
4. `map`
5. `validate`
6. `package`
7. `export`

An optional `run` command may execute the full pipeline end-to-end for a bounded
set of source URLs.

## Documentation

- [architecture](./docs/architecture.md)
- [cli](./docs/cli.md)
- [contracts](./docs/contracts.md)
- [source policy](./docs/source-policy.md)
- [review workflow](./docs/review-workflow.md)
- [test contract](./docs/test-contract.md)

## Examples

- [discovery manifest example](./examples/discovery-manifest.example.json)
- [source document example](./examples/source-document.example.yaml)
- [parsed fragment example](./examples/parsed-source-fragment.example.yaml)
- [semantic draft example](./examples/semantic-draft.example.yaml)
- [draft topic package example](./examples/draft-topic-package.example.yaml)
- [provenance sidecar example](./examples/provenance.example.json)
- [validation report example](./examples/validation-report.example.yaml)
