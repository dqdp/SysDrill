# Target Architecture v1

## Objective

Поставить text-first learning core, который:

- использует normalized knowledge base как source of truth;
- поддерживает `Study` / `Practice` / `Mock Interview`;
- использует `Session Intent` для remediation, spaced review и readiness checks;
- оценивает ответы по rubric и scenario bindings;
- сохраняет semantic interaction trail;
- строит learner profile;
- выбирает следующий structured learning action.

Этот документ описывает **implementation shape for v1**, а не только logical components.

## Architecture stance

v1 intentionally prefers:

- one deployable application backend;
- one web frontend;
- one relational database as primary system store;
- one async worker for projections and deferred evaluation/recommendation jobs;
- optional object storage for large transcripts / artifacts;
- no microservices by default.

Reason:
- strong schema and contract boundaries matter more than process boundaries in v1;
- recommendation, evaluation, runtime, and content all still benefit from monolith-speed iteration;
- async seams are introduced where consistency and latency requirements differ.

## Primary implementation seams

Even in a monolith-shaped v1, the codebase should preserve these seams:

1. `content_kernel`
2. `learning_design`
3. `session_runtime`
4. `evaluation_engine`
5. `event_log`
6. `learner_model_projection`
7. `recommendation_engine`
8. `web_api` / `frontend`

These are **module boundaries first**, not necessarily deployable services.

## Deployable topology v1

## 1. Frontend
Responsibilities:
- session UI for Study / Practice / Mock
- review surfaces
- learning path / recommendation surfaces
- weak-area dashboard

Talks to:
- application API only

## 2. Application Backend
Responsibilities:
- session orchestration
- content/query resolution
- evaluation submission and retrieval
- recommendation read / accept / completion APIs
- learner profile read APIs
- auth/session ownership checks
- emitting semantic events

This is the central process in v1.

## 3. Async Worker
Responsibilities:
- learner state projection
- deferred recommendation recomputation
- heavier evaluation tasks when not run inline
- generation of offline audit material
- review queue maintenance

The worker consumes persisted jobs/events from the primary store or queue abstraction.

## 4. Primary Relational Database
Responsibilities:
- canonical runtime data
- content metadata and materialized authoring artifacts
- sessions
- semantic event log
- evaluation results
- learner state projections
- recommendation decisions
- review artifacts
- version references to rubric/content/binding

## 5. Optional Object Storage
Used only if needed for:
- long transcripts
- exported audit artifacts
- large review bundles

v1 may keep everything in the relational store if payload sizes remain modest.

## Logical modules and responsibilities

## 1. Content Store
Owns runtime-readable representations of:
- concepts
- patterns
- scenarios
- canonical hint ladders
- rubrics
- scenario bindings
- learning-design templates

Suggested representation:
- Markdown/YAML in repository for authoring
- materialized DB model for runtime query

Read/write stance:
- runtime mostly reads
- authoring pipeline writes / refreshes materialized content

## 2. Session Orchestrator
Owns:
- session planning from a `StructuredLearningAction`
- state transitions defined in `session_runtime_state_machine_v1.md`
- unit delivery order within action bounds
- hint request handling
- answer boundary detection
- handoff to evaluation
- session completion / abandonment semantics

Does not own:
- learner state mutation
- recommendation ranking
- freeform curriculum logic

## 3. Tutor LLM Adapter
Used for:
- bounded hint rendering
- explanation rephrasing
- follow-up generation within allowed envelope
- review synthesis support
- parts of evaluation judgment where rubric permits

Boundary:
LLM is not source of truth and may not bypass rubric or policy constraints.

## 4. Evaluation Engine
Owns:
- rubric-first scoring pipeline
- criterion result assembly
- missing-dimension extraction
- evaluation confidence derivation
- normalized downstream signals for learner state updates
- review-oriented feedback payload generation

Depends on:
- `rubric_schema.md`
- `scenario_rubric_binding_v1.md`

## 5. Event Collector
Owns:
- append-only persistence of semantic learning events
- coarse timing summaries
- recommendation lifecycle events
- version references used by each session/evaluation

This is a system boundary, not just logging glue.

## 6. Learner Model Projector
Consumes:
- semantic events
- evaluation results
- recommendation outcomes

Produces:
- concept state projections
- subskill state projections
- trajectory state projections
- mock-readiness projection
- review-due projections

Runs:
- asynchronously by default
- may expose synchronous refresh hooks only when strictly needed for UX

## 7. Recommendation Engine
Consumes:
- projected learner state
- recent trajectory
- review-due signals
- action templates and policy constraints

Produces:
- `RecommendationDecision`
- bounded `StructuredLearningAction`

Boundary:
Recommendation engine does not micro-orchestrate turns inside a session.

## 8. Web Application
Text-first interface with:
- card view
- practice / scenario panel
- review page
- learning path page
- recommendation acceptance / skip actions

## Sync vs async boundaries

## Inline / synchronous path
Should stay synchronous for v1 UX:
- fetch next recommendation to show
- accept recommended action
- create session
- deliver next unit
- submit answer boundary
- attach evaluation if evaluation path is light enough
- show review when available

## Async / deferred path
Should be asynchronous by default:
- learner state projection
- recommendation recomputation after session completion
- heavy evaluation passes
- offline audit artifact generation
- maintenance queue updates

Rule:
inline path optimizes for bounded, understandable UX latency; async path owns recomputation and projections.

## Core runtime data flow

### Flow A — recommendation to session
1. Recommendation engine emits `RecommendationDecision`.
2. User accepts recommendation.
3. Session orchestrator creates session from `StructuredLearningAction`.
4. `session_started` and `unit_presented` are emitted.
5. Runtime executes state machine within action bounds.

### Flow B — session to evaluation
1. User submits answer boundary.
2. Session runtime emits semantic events.
3. Evaluation engine builds evaluation context from:
   - session mode / intent
   - executable unit
   - transcript
   - hint/reveal usage
   - completion flags
4. Evaluation result is persisted and linked to the session turn/unit.

### Flow C — evaluation to learner state
1. Evaluation result and relevant events are consumed by learner projector.
2. Projector updates concept / subskill / trajectory projections.
3. Review-due and mock-readiness projections are recalculated.

### Flow D — learner state to next recommendation
1. Recommendation engine consumes latest projections plus recommendation history.
2. Policy generates candidates, ranks them, applies guardrails.
3. New `RecommendationDecision` is persisted and optionally shown in UI.

## Persistence model v1

The relational store should have at least these logical tables/collections:

- `content_concepts`
- `content_patterns`
- `content_scenarios`
- `content_rubrics`
- `content_scenario_bindings`
- `learning_templates`
- `sessions`
- `session_units`
- `semantic_events`
- `evaluation_results`
- `review_reports`
- `learner_concept_state`
- `learner_subskill_state`
- `learner_trajectory_state`
- `recommendation_decisions`
- `recommendation_outcomes`
- `schema_versions` or version references embedded in records

This does not force exact physical names; it documents required data responsibilities.

## Transaction and consistency stance

v1 should prefer:
- strong consistency for session creation, semantic event append, evaluation result persistence, and recommendation decision persistence;
- eventual consistency for learner-state projections and derived dashboards;
- idempotent worker processing for projections and recommendation recomputation.

Important rule:
the event log is append-only and should remain reconstructable enough for audits and projector replays.

## Failure containment

### Runtime failure
- session may end as `abandoned`
- semantic event boundary still recorded if possible
- do not fabricate full-confidence evaluation

### Evaluation failure
- record evaluation failure state
- allow retry or degraded review path
- do not block event persistence

### Projection failure
- preserve raw events and evaluation results
- retry asynchronously
- recommendation may temporarily rely on last stable learner projection

### Recommendation failure
- fall back to safe deterministic baseline actions
- do not block session continuation on recommendation-only issues

## Implementation slices

### Slice 1 — text learning spine
- content materialization
- Study mode
- semantic event logging
- basic evaluation
- concept-level learner state
- baseline deterministic recommendation

### Slice 2 — applied reasoning
- Practice mode
- scenario bindings
- stronger evaluation output
- subskill projections
- recommendation rationale and history

### Slice 3 — readiness loop
- Mock Interview mode
- stricter runtime profile
- mock readiness projection
- review-due maintenance and weak-area dashboard

## Non-goals for v1 architecture
- microservice decomposition by default
- streaming/event-bus-first infrastructure
- separate voice service as foundational dependency
- online learning model deciding recommendation policy
- opaque evaluation pipeline without rubric provenance

## Key contract dependencies

This architecture assumes the following documents remain authoritative:
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/learner_state_update_rules_v1.md`
- `docs/03_architecture/recommendation_policy_v1.md`
- `docs/03_architecture/recommendation_engine_surface.md`
