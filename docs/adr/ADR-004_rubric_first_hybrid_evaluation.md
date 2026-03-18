# ADR-004: Rubric-first Hybrid Evaluation

Date: 2026-03-17  
Status: Accepted

## Context

Pure LLM scoring непрозрачен и плохо подходит как основа learner model.

## Decision

Оценка строится как hybrid:
- rubric defines the shape of judgment;
- rules capture explicit signals;
- LLM assists where nuanced reasoning is needed.

## Consequences

### Positive
- выше explainability;
- learner model получает структурированные signals;
- легче обсуждать fairness of scoring.

### Negative
- implementation сложнее, чем одно свободное prompt-based score;
- требуется поддерживать rubric evolution.
