# Scenario Rubric Binding v1

## Purpose

Этот документ связывает глобальную rubric schema с конкретными families
сценариев. Он задаёт:
- какие критерии обязательны;
- какие вторичны;
- какие веса применяются;
- какие hard gating conditions существуют;
- как mode меняет строгость.

## Binding model

Каждый binding определяет:
- `binding_id`
- `scenario_family`
- `required_criteria`
- `secondary_criteria`
- `not_applicable_criteria`
- `criterion_weights`
- `gating_conditions`
- `mode_adjustments`
- `expected_evidence_cues`

## Shared aggregation rules

### Weighted score
Используется формула из `rubric_schema.md`:

`weighted_score = sum(normalized_score * weight) / sum(applicable_weights)`

### Passing guidance by mode

#### Study Mode
- no hard pass/fail;
- focus on criterion gaps and formative feedback;
- gating failures still visible, but do not block continuation.

#### Practice Mode
Guidance threshold:
- `weighted_score >= 0.55`
- no more than one required criterion at `0`
- no unresolved hard gating failure

#### Mock Interview Mode
Guidance threshold:
- `weighted_score >= 0.65`
- no required criterion at `0`
- no hard gating failure
- `trade_off_articulation` and `communication_clarity` should be at least `2`
  for scenarios where they are required

## Global criterion ids

- `requirements_understanding`
- `decomposition_quality`
- `data_and_storage_choices`
- `scaling_strategy`
- `reliability_awareness`
- `trade_off_articulation`
- `communication_clarity`

## Scenario family bindings

## 1. URL Shortener

### Binding id
`binding.url_shortener.v1`

### Required criteria
- `requirements_understanding`
- `decomposition_quality`
- `data_and_storage_choices`
- `scaling_strategy`
- `trade_off_articulation`

### Secondary criteria
- `reliability_awareness`
- `communication_clarity`

### Weights
- requirements_understanding: `1.0`
- decomposition_quality: `1.2`
- data_and_storage_choices: `1.2`
- scaling_strategy: `1.2`
- trade_off_articulation: `1.0`
- reliability_awareness: `0.7`
- communication_clarity: `0.7`

### Gating conditions
Hard failure if answer misses all of the following:
- id generation or collision avoidance;
- redirect/read path scaling;
- storage choice for mapping short id -> long URL.

### Expected evidence cues
- read-heavy workload awareness;
- cache placement;
- storage/index choice;
- short id generation discussion.

## 2. Rate Limiter

### Binding id
`binding.rate_limiter.v1`

### Required criteria
- `requirements_understanding`
- `decomposition_quality`
- `data_and_storage_choices`
- `reliability_awareness`
- `trade_off_articulation`

### Secondary criteria
- `scaling_strategy`
- `communication_clarity`

### Weights
- requirements_understanding: `1.1`
- decomposition_quality: `1.0`
- data_and_storage_choices: `1.2`
- reliability_awareness: `1.2`
- trade_off_articulation: `1.0`
- scaling_strategy: `0.8`
- communication_clarity: `0.7`

### Gating conditions
Hard failure if answer misses all of the following:
- state placement / counting strategy;
- algorithm choice or rate-limiting semantics;
- failure handling when state store is unavailable or lagging.

### Expected evidence cues
- token bucket / leaky bucket / fixed-window trade-offs;
- centralized vs distributed counters;
- correctness vs latency trade-offs.

## 3. Chat System

### Binding id
`binding.chat_system.v1`

### Required criteria
- `requirements_understanding`
- `decomposition_quality`
- `data_and_storage_choices`
- `scaling_strategy`
- `reliability_awareness`
- `trade_off_articulation`
- `communication_clarity`

### Weights
- requirements_understanding: `1.1`
- decomposition_quality: `1.2`
- data_and_storage_choices: `1.0`
- scaling_strategy: `1.2`
- reliability_awareness: `1.1`
- trade_off_articulation: `1.1`
- communication_clarity: `0.9`

### Gating conditions
Hard failure if answer misses all of the following:
- delivery semantics or ordering discussion;
- fanout / message distribution path;
- online/offline state or message persistence discussion.

### Expected evidence cues
- real-time transport path;
- message storage and sync;
- ordering / duplication / retries;
- group chat scaling implications.

## 4. Notification System

### Binding id
`binding.notification_system.v1`

### Required criteria
- `requirements_understanding`
- `decomposition_quality`
- `scaling_strategy`
- `reliability_awareness`
- `trade_off_articulation`

### Secondary criteria
- `data_and_storage_choices`
- `communication_clarity`

### Weights
- requirements_understanding: `1.1`
- decomposition_quality: `1.1`
- scaling_strategy: `1.2`
- reliability_awareness: `1.2`
- trade_off_articulation: `1.0`
- data_and_storage_choices: `0.8`
- communication_clarity: `0.7`

### Gating conditions
Hard failure if answer misses all of the following:
- asynchronous delivery pipeline;
- retries / idempotency or duplicate prevention;
- channel-specific delivery concerns or user preferences.

### Expected evidence cues
- queue-based decoupling;
- fanout to channels;
- provider failures;
- delivery guarantees and opt-out handling.

## 5. News Feed

### Binding id
`binding.news_feed.v1`

### Required criteria
- `requirements_understanding`
- `decomposition_quality`
- `data_and_storage_choices`
- `scaling_strategy`
- `trade_off_articulation`

### Secondary criteria
- `reliability_awareness`
- `communication_clarity`

### Weights
- requirements_understanding: `1.1`
- decomposition_quality: `1.1`
- data_and_storage_choices: `1.2`
- scaling_strategy: `1.2`
- trade_off_articulation: `1.1`
- reliability_awareness: `0.7`
- communication_clarity: `0.7`

### Gating conditions
Hard failure if answer misses all of the following:
- push vs pull or fanout strategy discussion;
- feed storage / ranking path discussion;
- hot-user or celebrity problem awareness.

### Expected evidence cues
- precompute vs on-read trade-offs;
- timeline generation path;
- caching and ranking implications.

## 6. Media / File Delivery

### Binding id
`binding.media_delivery.v1`

### Required criteria
- `requirements_understanding`
- `decomposition_quality`
- `data_and_storage_choices`
- `scaling_strategy`
- `reliability_awareness`

### Secondary criteria
- `trade_off_articulation`
- `communication_clarity`

### Weights
- requirements_understanding: `1.0`
- decomposition_quality: `1.1`
- data_and_storage_choices: `1.3`
- scaling_strategy: `1.2`
- reliability_awareness: `1.0`
- trade_off_articulation: `0.8`
- communication_clarity: `0.7`

### Gating conditions
Hard failure if answer misses all of the following:
- upload/download path distinction;
- object storage or durable media store;
- CDN / edge delivery or large-file serving strategy.

### Expected evidence cues
- signed URLs or access control path;
- chunking / resumable upload awareness;
- media processing or replication discussion where relevant.

## Mode adjustments

### Study Mode
- downgrade communication severity by one level in summary interpretation;
- allow partial coverage without turning it into fail framing;
- preserve gating visibility, but present it as missing area rather than failure verdict.

### Practice Mode
- use weights as defined above;
- keep gating visible and actionable;
- surface one primary remediation target and at most two secondary gaps.

### Mock Interview Mode
- keep weights as defined above;
- no downgrade for communication or trade-offs;
- missing required criterion at `0` should strongly affect overall summary;
- hard gating failure should block "ready" verdict.

## Notes

1. Эти bindings — v1 guidance, а не окончательная психометрика.
2. Цель bindings — сделать evaluation reproducible enough for implementation.
3. Новые scenario families должны добавляться отдельным binding,
   а не скрытым prompt tweak inside evaluator.
