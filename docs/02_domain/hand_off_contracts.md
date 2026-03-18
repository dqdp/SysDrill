# Hand-off Contracts

This document defines what passes between bounded contexts and which invariants must hold across those boundaries.

## Contract 1 — Content Kernel -> Learning Design
### Purpose
Pass canonical knowledge objects for pedagogical transformation.

### Input
- `Concept` / `Pattern` / `Scenario`
- prerequisites and topic relations
- canonical explanation
- trade-off metadata
- `HintLadder`
- canonical follow-up candidates
- baseline content difficulty

### Output
- source-aware design input
- pedagogical goal
- candidate `Card` / `ExerciseTemplate`
- difficulty transform
- hint-policy binding seed
- follow-up envelope seed

### Invariants
- canonical meaning is preserved
- source traceability is not lost
- baseline difficulty is not silently mutated

## Contract 2 — Learning Design -> Session Runtime
### Purpose
Pass an executable learning unit for a bounded session.

### Output
- `ExecutableLearningUnit`
- visible prompt
- pedagogical goal
- mode and session intent
- effective difficulty
- allowed hint policy
- follow-up envelope
- completion rules
- evaluation binding id

### Invariants
- runtime receives a formed unit, not raw knowledge text
- runtime may order units, but may not redefine pedagogical intent
- remediation and spaced review remain intents, not top-level modes

## Contract 3 — Session Runtime -> Evaluation Engine
### Purpose
Pass a stable answer boundary for scoring.

### Input
- session mode and intent
- unit id and evaluation binding id
- user transcript
- hints used
- timing signals
- completion / abandon flags

### Output
- `EvaluationResult`
- criterion results
- missing dimensions
- gating failures
- evidence snippets
- summary feedback draft
- normalized downstream signals

### Invariants
- evaluation is always rubric/binding aware
- evaluation does not rewrite transcript
- partial transcripts reduce confidence rather than producing full-confidence scores

## Contract 4 — Session Runtime -> Interaction Log
### Purpose
Record facts of interaction, not interpretation.

### Output
- append-only `InteractionEvent`
- event type
- timestamp
- session / unit / content ids
- raw payload
- actor, mode, and intent metadata

### Invariants
- events are not rewritten after append
- derived learner state is not back-written as raw event

## Contract 5 — Evaluation Engine -> Learning Intelligence
### Purpose
Pass quality signals for learner-state updates.

### Output
- normalized criterion signals
- weak dimensions
- confidence note
- score provenance
- gating failures
- update inputs for concept/subskill/trajectory state

### Invariants
- Learning Intelligence does not mutate historical evaluation results
- downstream use must respect confidence and evidence density

## Contract 6 — Learning Intelligence -> Session Runtime
### Purpose
Pass the next bounded learning action.

### Output
A `RecommendationAction` with:
- `mode`
- `session_intent`
- `target_type`
- `target_id`
- `difficulty_profile`
- `strictness_profile`
- `session_size`
- `delivery_profile`
- `rationale`

### Invariants
- recommendation plans the next session; it does not mutate the current one
- rationale is mandatory
- runtime expands the action into exact unit ordering and turn-level orchestration
- recommendation does not own hint timing, per-turn follow-ups, or runtime recovery logic

## Contract 7 — System -> Interaction Layer
### Purpose
Render units, review artifacts, and recommendations to the learner.

### Output
- prompt/card/scenario
- hint controls
- progress state
- review report
- recommendation with explanation

### Invariants
- UI does not own recommendation or scoring semantics
- rendering must preserve domain identifiers and traceability
- client events must remain compatible with the semantic interaction model
