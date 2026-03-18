# ADR-007: Semantic event granularity for v1

Date: 2026-03-18  
Status: Accepted

## Context

После фиксации structured recommendation action scope нужно было определить,
какой именно interaction trail обязателен для learner model, recommendation
policy и assurance.

Слишком грубая event model (только session result или final score) делает
невозможными:
- explainable learner state updates;
- recommendation feedback loops;
- distinction between struggle, hint reliance, reveal, and abandonment.

Слишком детальная raw UI telemetry для v1 тоже нежелательна, потому что она:
- увеличивает storage and processing complexity;
- смешивает product analytics with learner evidence;
- создаёт шумные сигналы с низкой педагогической ценностью.

## Decision

В v1 система логирует **semantic learning events** на границах:
- session lifecycle;
- learning unit exposure and learner response;
- hint/reveal/follow-up behavior;
- evaluation and review surfaces;
- recommendation lifecycle.

Event model v1 **не** делает first-class learner events из:
- low-level typing telemetry;
- per-edit UI exhaust;
- raw voice partials / ASR interim hypotheses;
- hover / scroll / cosmetic UI actions.

Допускаются только coarse timing fields и агрегированные duration metrics,
которые directly support learner interpretation or assurance.

## Consequences

### Positive
- learner model получает достаточно rich evidence without UI noise;
- recommendation effectiveness становится traceable;
- assurance остаётся explainable and auditable;
- v1 implementation complexity stays bounded.

### Trade-offs
- некоторые later-stage UX/product analytics сигналы не будут доступны сразу;
- deeper hesitation or drafting analysis откладывается до later versions;
- voice-specific fine-grained telemetry потребует отдельного future design.

## Required semantic event families

### Session lifecycle
- `session_planned`
- `session_started`
- `session_completed`
- `session_abandoned`

### Learning unit interaction
- `unit_presented`
- `answer_submitted`
- `hint_requested`
- `answer_revealed`
- `follow_up_presented`
- `follow_up_answered`

### System interpretation surfaces
- `evaluation_attached`
- `review_presented`

### Recommendation lifecycle
- `recommendation_generated`
- `recommendation_shown`
- `recommendation_accepted`
- `recommendation_skipped`
- `recommendation_completed`

## Rejected alternatives

### Alternative A — final-score-only telemetry
Отклонено, потому что она слишком бедна для learner profile и recommendation policy.

### Alternative B — log all UI exhaust as learner evidence
Отклонено, потому что это prematurely increases complexity and mixes
learning semantics with implementation noise.
