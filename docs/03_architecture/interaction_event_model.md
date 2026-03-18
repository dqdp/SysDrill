# Interaction Event Model

## Why an event model exists

Для персонализированного обучения недостаточно хранить:

- только итоговый score;
- только последний ответ;
- только “успешно/неуспешно”.

Нужен append-only журнал фактов взаимодействия.

## Event granularity principle

В v1 система логирует **semantic learning events**, а не полный UI exhaust.
Событие должно помогать хотя бы одной из трёх задач:

- обновление learner state;
- объяснимая recommendation policy;
- assurance / traceability.

Поэтому в v1 event model intentionally excludes first-class events for:
- low-level typing telemetry;
- per-edit draft exhaust;
- hover / scroll / cosmetic UI actions;
- raw voice partials and interim ASR hypotheses.

## Design principles

1. Событие фиксирует **факт**, а не итоговую интерпретацию.
2. Событие не переписывается задним числом.
3. Интерпретация и projection идут downstream.
4. Каждое событие должно быть пригодно для traceability.
5. Время в v1 хранится как coarse timing summary, а не как детальная микротелеметрия.

## Required fields

- `event_id`
- `event_type`
- `user_id`
- `session_id`
- `mode`
- `session_intent`
- `content_id` (nullable for some recommendation-only events)
- `occurred_at`
- `payload`
- `source` (`web`, later `voice`)
- `trace_id`

## Optional timing fields

- `response_latency_ms`
- `session_duration_ms`
- `time_to_hint_ms`
- `voice_answer_duration_ms` (later, if applicable)

These fields are allowed only as **coarse summaries**.

## Core event families and types

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

## Required semantic meaning

### `answer_submitted`
Represents one meaningful learner response against one learning unit or follow-up.
It should reference the final submitted transcript/text, not intermediate drafts.

### `hint_requested`
Represents a learner request for more guidance. The payload must record hint level
and cumulative hint count for the unit when available.

### `answer_revealed`
Represents the decision to reveal canonical or near-canonical help/answer content.
This is a strong pedagogical signal and must remain distinct from `unit_presented`.

### `evaluation_attached`
Represents the system judgment attached to a learner attempt. It should remain
separate from interaction events so evidence and judgment can be audited independently.

## Payload examples

### `hint_requested`
```json
{
  "hint_level": 2,
  "hint_count_for_unit": 2,
  "reason": "stuck_on_scaling",
  "time_to_hint_ms": 18000
}
```

### `answer_submitted`
```json
{
  "response_modality": "text",
  "char_count": 820,
  "response_latency_ms": 54000,
  "submission_kind": "manual_submit",
  "used_prior_hints": true,
  "follow_up_context": false
}
```

### `recommendation_accepted`
```json
{
  "decision_id": "rec_123",
  "recommended_mode": "practice",
  "recommended_intent": "Remediate",
  "target_type": "skill",
  "target_id": "tradeoff_articulation",
  "difficulty_profile": "medium",
  "strictness_profile": "standard",
  "session_size": "1_mini_drill"
}
```

## Derived signals built downstream

Из events вычисляются:

- time to submission;
- time to first hint (if available);
- hint dependency;
- reveal dependency;
- abandon rate;
- review engagement;
- repeated weakness frequency;
- spaced review compliance;
- recommendation completion rate by action type.

## What is intentionally out of scope for v1

- keypress-level telemetry;
- per-edit drafting history;
- cursor/focus exhaust;
- raw audio as learner evidence primitive;
- interim ASR/VAD event streams in learner profile projection.

These may exist in separate product analytics or infrastructure logs later,
but they are not first-class learner events in v1.

## Storage note

На старте достаточно relational storage with append-only discipline.
Слишком ранний переход к event streaming infra не обязателен.

## Privacy / future note

Если появится voice:
- raw audio не должен быть обязательным для learner profile;
- предпочтительно хранить transcript + derived coarse metrics;
- retention raw audio должен быть отдельно регулируем.
