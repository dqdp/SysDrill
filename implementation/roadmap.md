# TDD Roadmap

Execution posture:
- preserve the v2.2 implementation baseline
- keep bounded contexts separate
- prefer thin, verifiable slices over broad scaffolding
- use exported file bundles as the first hand-off from tooling to backend

## Minimal prototype target

The fastest acceptable prototype is:
- a manually launched `Study` or `Practice` session
- resolved from a materialized `ExecutableLearningUnit`, not raw topic bundles
- with one bounded answer submission path
- append-only semantic events
- deterministic review output
- a thin frontend shell or API-driven demo path

The first prototype does not require recommendation-driven session start.

## Milestones

### Milestone A. Content-backed foundation

Includes:
- `001. Importer exporter MVP`
- `002. Content bundle reader`
- `003. Content catalog API surface`
- `003a. Content catalog hardening`
- `004. Executable learning unit materialization`

Exit criteria:
- backend can load content, expose a read-only catalog, and materialize bounded
  `ExecutableLearningUnit` shapes

Status:
- completed in current worktree

### Milestone B. Manual end-to-end prototype

Goal:
- reach the first demoable learner loop without waiting on recommendation

Fast-path execution order:
1. `005. Session runtime and event log bootstrap`
2. `006. Rule-first evaluation loop`
3. `008. Practice frontend shell`

Expected narrow implementation steps inside this milestone:
- manual session start over one materialized unit
- answer submission and deterministic turn closure
- append-only semantic event persistence
- deterministic concept-recall review artifact
- thin manual launcher plus answer/review UI

Exit criteria:
- one learner can manually launch a session, answer a bounded unit, and receive
  deterministic review through the backend and a thin UI or equivalent demo

Status:
- next critical milestone

### Milestone C. Guided next-step prototype

Includes:
- `007. Recommendation placeholder`

Goal:
- replace manual launch with a deterministic next-step recommendation

Exit criteria:
- recommendation returns one bounded action and runtime can start from that
  action without changing the Milestone B loop semantics

Status:
- pending until Milestone B is demoable

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
- completed

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
- completed

Goal:
- expose loaded content through minimal read-only backend endpoints

Likely endpoints:
- `GET /content/topics`
- `GET /content/topics/{slug}`

### 003a. Content catalog hardening

Status:
- completed

Goal:
- harden content loading so invalid configured roots and malformed bundles fail
  closed with explicit errors

Why now:
- review found narrow correctness gaps in slices 002 and 003
- closing them now preserves the current startup contract before later runtime
  slices depend on it

### 004. Executable learning unit materialization

Status:
- completed

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

Prototype dependency:
- not required for the first manual working prototype
- should start only after Milestone B is demoable

Guardrail:
- recommendation must stay a structured action surface, even if the first
  version is rule-based and narrow

### 008. Practice frontend shell

Status:
- pending

Goal:
- connect the complex TS frontend to the minimal backend loop

Prototype priority:
- may start after `006` and before `007` to reach a visible prototype sooner

Fallback posture:
- if frontend work starts earlier, it should use explicit manual session launch
  and must not invent recommendation semantics in the UI

## Replanning rule

Reorder slices only when one of the following is true:
- a completed slice reveals a contract mismatch with the knowledge base
- a blocking implementation dependency was missed
- a narrower slice can retire a larger execution risk faster
