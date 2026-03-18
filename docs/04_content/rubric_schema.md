# Rubric Schema

## Purpose

Rubric задаёт **исполняемый контракт оценки**: общий каталог критериев,
форму criterion result и правила агрегации. Он нужен не только для human review,
но и для воспроизводимого evaluation pipeline.

Этот документ описывает глобальную схему rubric.
Scenario-specific applicability, веса и gating rules задаются отдельно
в `scenario_rubric_binding_v1.md`.

## Global criteria catalog

### 1. Requirements understanding
Пользователь выявил ключевые требования и ограничения.

Typical signals:
- addresses scale, latency, availability or consistency needs;
- surfaces edge constraints or abuse vectors where relevant;
- не отвечает в вакууме без попытки определить рамки задачи.

### 2. Decomposition quality
Пользователь разбил систему на осмысленные части.

Typical signals:
- clear components and responsibilities;
- understandable data flow;
- no random component dumping.

### 3. Data and storage choices
Пользователь выбрал storage и объяснил последствия.

Typical signals:
- fit to access pattern;
- indexing / partitioning awareness;
- durability or consistency implications.

### 4. Scaling strategy
Пользователь видит bottlenecks и масштабирование.

Typical signals:
- stateless scaling where relevant;
- caching/CDN/queue usage when justified;
- partitioning, fanout or backpressure awareness.

### 5. Reliability awareness
Пользователь говорит о failure modes и operations.

Typical signals:
- retries / idempotency;
- monitoring / alerts;
- degraded modes / recovery thinking.

### 6. Trade-off articulation
Пользователь сравнивает варианты и объясняет выбор.

Typical signals:
- explicit alternative considered;
- cost/performance/consistency trade-offs surfaced;
- avoids one-true-design tone.

### 7. Communication clarity
Пользователь говорит структурированно и interview-readable.

Typical signals:
- clear progression;
- concise but complete explanation;
- answer is easy to follow and audit.

## Criterion result contract

Каждый criterion result должен содержать:
- `criterion_id`
- `applicability`
- `weight`
- `score_band`
- `observed_evidence`
- `missing_aspects`
- `inferred_judgment`
- `criterion_confidence`

### Applicability values
- `required`
- `secondary`
- `not_applicable`

### Evidence separation rule

`observed_evidence` и `inferred_judgment` должны храниться отдельно.

- `observed_evidence` — что действительно было в ответе;
- `inferred_judgment` — интерпретация evaluator-а.

Это разделение обязательно. Без него система не сможет объяснять scoring
и тестировать consistency.

## Score bands

### 0 — Missing
Критерий практически не покрыт или покрыт ошибочно.

### 1 — Weak
Есть слабые следы, но без рабочей глубины или связности.

### 2 — Adequate
Критерий покрыт на приемлемом уровне для текущего режима.

### 3 — Strong
Критерий покрыт уверенно, связно и с достаточной глубиной.

## Normalization rule

Для downstream aggregation используется:

`normalized_score = score_band / 3`

Следствия:
- `0 -> 0.00`
- `1 -> 0.33`
- `2 -> 0.67`
- `3 -> 1.00`

## Aggregation contract

Глобальная схема поддерживает weighted aggregation по применимым критериям.
Сами веса задаются binding-ом.

### Base formula

`weighted_score = sum(normalized_score * weight) / sum(applicable_weights)`

Where:
- criteria with `not_applicable` are excluded;
- `required` and `secondary` are both included, but may have different weights;
- hard gating failures are handled outside raw weighted score.

## Gating concept

Некоторые scenario-family bindings могут задавать hard failures.
Например, в `chat system` можно считать hard failure отсутствие discussion
про delivery semantics или fanout path.

Gating failures:
- не заменяют criterion scores;
- не должны прятаться внутри summary comment;
- должны быть явно перечислены в evaluation result.

## Confidence semantics

Rubric result must include:
- `overall_confidence` from `0.0` to `1.0`;
- per-criterion `criterion_confidence`;
- optional `confidence_notes`.

Confidence should go down when:
- answer is partial or interrupted;
- transcript is too short;
- high-level hints leaked a large portion of the answer;
- mode or capture quality limits observability.

## Output contract

Rubric result must include:
- `rubric_version`
- `binding_id`
- `criterion_results[]`
- `weighted_score`
- `gating_failures[]`
- `overall_confidence`
- `summary_comment`
- `downstream_signals`

### Downstream signals may include
- `coverage_gap`
- `tradeoff_gap`
- `reliability_gap`
- `communication_gap`
- `strong_independent_performance`
- `hint_dependency`

## Non-goals of rubric schema

Этот документ не определяет:
- какой scenario family к чему относится;
- какие веса у `URL shortener` vs `chat system`;
- какой threshold считать passing в Practice или Mock.

Это задаётся в `scenario_rubric_binding_v1.md`.
