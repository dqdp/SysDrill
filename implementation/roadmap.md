# TDD Roadmap

Execution posture:
- preserve the v2.2 implementation baseline
- keep bounded contexts separate
- prefer thin, verifiable slices over broad scaffolding
- use exported file bundles as the first hand-off from tooling to backend

## Ordered slices

### 001. Importer exporter MVP

Status:
- completed

Goal:
- produce usable exported topic bundles from `system-design.space`

Output:
- `topic-package.yaml`
- `provenance.json`
- `validation-report.json`

### 002. Content bundle reader

Status:
- next

Goal:
- load exported topic bundles into the backend from the filesystem

Why now:
- this closes the first concrete hand-off between tooling and product runtime
- it lets backend integration start without inventing a database-backed content
  path too early

Guardrail:
- draft exporter bundles are for explicit internal/dev ingestion first, not an
  automatic production publishing contract

### 003. Content catalog API surface

Status:
- pending

Goal:
- expose loaded content through minimal read-only backend endpoints

Likely endpoints:
- `GET /content/topics`
- `GET /content/topics/{slug}`

### 004. Executable learning unit materialization

Status:
- pending

Goal:
- transform loaded content plus learning-design metadata into bounded
  `ExecutableLearningUnit` shapes without collapsing `Content Kernel` and
  `Learning Design`

Why before runtime:
- runtime should orchestrate concrete learning units, not raw topic bundles

### 005. Session runtime and event log bootstrap

Status:
- pending

Goal:
- create the minimal backend surface for session creation, answer submission,
  and append-only semantic event emission

### 006. Rule-first evaluation loop

Status:
- pending

Goal:
- produce deterministic review output for one bounded scenario family

### 007. Recommendation placeholder

Status:
- pending

Goal:
- add deterministic next-step selection over the loaded content set

Guardrail:
- recommendation must stay a structured action surface, even if the first
  version is rule-based and narrow

### 008. Practice frontend shell

Status:
- pending

Goal:
- connect the complex TS frontend to the minimal backend loop

Fallback posture:
- if frontend work starts earlier, it should use explicit manual session launch
  and must not invent recommendation semantics in the UI

## Replanning rule

Reorder slices only when one of the following is true:
- a completed slice reveals a contract mismatch with the knowledge base
- a blocking implementation dependency was missed
- a narrower slice can retire a larger execution risk faster
