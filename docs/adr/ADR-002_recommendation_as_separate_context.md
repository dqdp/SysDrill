# ADR-002: Recommendation as a Separate Bounded Context

Date: 2026-03-17  
Status: Accepted

## Context

Простое сохранение истории сессий не решает задачу адаптивного обучения.
Нужна отдельная логика построения learner profile и выбора next-best-action.

## Decision

Recommendation выделяется в отдельный bounded context `Learning Intelligence`.

Он получает:
- interaction events;
- evaluation outputs;
- time-gap signals.

Он производит:
- learner profile updates;
- review queue;
- recommendation decisions with rationale.

## Consequences

### Positive
- персонализация не смешивается с runtime;
- появляется explainability;
- recommendation можно улучшать независимо.

### Negative
- появляется дополнительный projection / policy layer;
- нужно поддерживать rationale logging.
