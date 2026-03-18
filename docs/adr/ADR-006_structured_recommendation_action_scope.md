# ADR-006: Recommendation selects a structured learning action

Date: 2026-03-18  
Status: Accepted

## Context

После фиксации top-level modes и session intent оставалась развилка: recommendation
должен выбирать только следующий content item или следующий учебный ход целиком.

Для System Design Trainer выбор только content item слишком слаб, потому что
ценность продукта состоит не только в выборе темы, но и в выборе формы дальнейшей
тренировки: remediation, reinforcement, spaced review, readiness check, guided vs stricter session.

Полностью свободный pedagogical agent тоже нежелателен для v1, потому что он
создаёт opaque policy surface и размывает ответственность между recommendation
и session runtime.

## Decision

Recommendation в v1 выбирает **structured learning action**, а не только content item.

Action contract включает:
- `mode`
- `session_intent`
- `target_type`
- `target_id`
- `difficulty_profile`
- `strictness_profile`
- `session_size`
- optional `delivery_profile`
- `rationale`

Recommendation не выбирает:
- точный prompt text;
- hint timing внутри сессии;
- exact follow-up sequence;
- runtime recovery branches;
- voice turn mechanics.

Эти responsibilities принадлежат Session Runtime и его policy profiles.

## Consequences

### Positive
- recommendation начинает отражать реальную педагогическую ценность продукта;
- action space остаётся bounded и explainable;
- Session Runtime сохраняет ответственность за micro-orchestration;
- analytics и assurance могут анализировать эффективность по action types, а не только по topics.

### Trade-offs
- action contract становится богаче;
- telemetry должна фиксировать acceptance / completion recommendation actions;
- learner model и policy должны оперировать mode + intent + profile, а не только темами.

## Rejected alternatives

### Alternative A — recommend only content items
Отклонено, потому что это превращает систему в более слабую adaptive content picker
и не использует её педагогическую differentiation.

### Alternative B — fully autonomous pedagogical agent
Отклонено, потому что это слишком расширяет policy surface v1, ухудшает explainability
и размывает boundary между recommendation и runtime orchestration.
