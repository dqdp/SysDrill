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
3. `006b. GitHub CI and smoke verification`
4. `008. Practice frontend shell`

Expected narrow implementation steps inside this milestone:
- manual session start over one materialized unit
- answer submission and deterministic turn closure
- append-only semantic event persistence
- deterministic concept-recall review artifact
- GitHub-native verification plus bounded smoke coverage for the prototype seam
- thin manual launcher plus answer/review UI

Exit criteria:
- one learner can manually launch a session, answer a bounded unit, and receive
  deterministic review through the backend and a thin UI or equivalent demo

Status:
- completed in current worktree

### Milestone C. Content enrichment and guided next-step prototype

Includes:
- `006c0. Bounded corpus acquisition and quality sweep`
- `006c. Practice prompt expansion`
- `006d. Concept field extraction hardening`
- `006e. Scenario draft seeding`
- `007. Recommendation placeholder`

Goal:
- acquire a wider bounded corpus, improve concept-field quality, make
  `Practice` meaningfully different from `Study`, seed the first conservative
  scenario drafts, then replace manual launch with a deterministic next-step
  recommendation

Exit criteria:
- a wider bounded corpus is imported and backend-compatible
- concept bundles expose meaningfully better `when_to_use` / `tradeoffs`
  coverage than the current placeholder baseline
- at least one valid scenario draft can be seeded from explicit source material
- `Practice` launchable units are visibly richer than `Study` without changing
  the current runtime/evaluation contracts
- recommendation returns one bounded action and runtime can start from that
  action without changing the Milestone B loop semantics

Status:
- completed in current worktree

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
- completed

Goal:
- create the minimal backend surface for session creation, answer submission,
  and append-only semantic event emission

### 006. Rule-first evaluation loop

Status:
- completed

Goal:
- produce deterministic review output for one bounded executable-unit family,
  `concept_recall`

### 006a. Runtime and loader review hardening

Status:
- completed

Goal:
- close narrow review-discovered correctness gaps in runtime concurrency,
  export-root validation, content summary projection, and health-only bootstrap

Why now:
- these are contract-preserving hardening fixes on the critical prototype path
- closing them before frontend work reduces avoidable demo-path instability

### 006b. GitHub CI and smoke verification

Status:
- completed

Goal:
- add GitHub-native verification plus bounded smoke checks for the current
  backend and importer prototype seam

Why now:
- the repository has local tests but no GitHub verification workflow yet
- current prototype work should be protected by a clean-environment install path
  and a small number of deterministic smoke checks before frontend integration

### 007. Recommendation placeholder

Status:
- completed in current worktree

Goal:
- add deterministic next-step selection over the loaded content set

Prototype dependency:
- not required for the first manual working prototype
- should start only after Milestone B is demoable

Guardrail:
- recommendation must stay a structured action surface, even if the first
  version is rule-based and narrow

Delivered:
- deterministic recommendation engine over the current concept-action surface
- runtime start-from-recommendation seam with structured action validation
- recommendation-first frontend happy path with manual fallback preserved
- append-only runtime events only for acceptance/completion boundaries
- green backend, frontend, and smoke verification

### 006c0. Bounded corpus acquisition and quality sweep

Status:
- completed in current worktree

Goal:
- gather a materially larger bounded corpus from `system-design.space` and
  measure its structural quality before changing backend learning-design
  behavior

Why now:
- current product feedback is dominated by an undersized content sample
- a larger bounded corpus gives a more reliable basis for `Practice` prompt
  differentiation and later recommendation work

### 006c. Practice prompt expansion

Status:
- completed in current worktree

Goal:
- enrich the current `Practice` prompt framing so it is more applied and more
  visibly different from `Study` while preserving the existing
  `concept_recall` binding, runtime loop, and API surface

Why before recommendation:
- current launcher feedback shows that `Practice` and `Study` are too similar
  to be productively recommended as distinct next-step actions
- recommendation should sit on top of a more meaningful action space, not paper
  over a weak unit shape
- this slice should follow `006c0`, not precede corpus acquisition

### 006d. Concept field extraction hardening

Status:
- completed in current worktree

Goal:
- improve importer-side extraction for `when_to_use`, `tradeoffs`, and
  `why_it_matters` so exported concept bundles are less sparse and less
  duplicative without changing product contracts

Why before recommendation:
- recommendation should not be planned on top of concept fields that are mostly
  empty or duplicated placeholders
- this slice improves the concept substrate for later scenario seeding and
  recommendation logic

### 006e. Scenario draft seeding

Status:
- completed in current worktree

Goal:
- seed the first conservative `Scenario` content objects from explicitly
  problem-like source pages without synthesizing scenarios from ordinary concept
  chapters

Why before recommendation:
- the content kernel is still scenario-empty today
- this slice tests whether the current source corpus supports honest scenario
  extraction before recommendation or later runtime work starts depending on
  scenario-bearing content

Outcome:
- first conservative scenario seeding path is now proven for explicit
  example/problem material
- scenario completeness is validator-enforced
- current runtime/evaluation remain unchanged, so recommendation still follows
  over the existing executable concept-action space

### 008. Practice frontend shell

Status:
- completed

Goal:
- connect the complex TS frontend to the minimal backend loop

Prototype priority:
- should start after `006b` so the current backend loop is protected by GitHub
  verification before frontend wiring expands the surface area

Fallback posture:
- if frontend work starts earlier, it should use explicit manual session launch
  and must not invent recommendation semantics in the UI

## Replanning rule

Reorder slices only when one of the following is true:
- a completed slice reveals a contract mismatch with the knowledge base
- a blocking implementation dependency was missed
- a narrower slice can retire a larger execution risk faster
