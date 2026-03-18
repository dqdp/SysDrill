# ADR-005: Three top-level runtime modes and separate session intent

Date: 2026-03-18  
Status: Accepted

## Context

Ранняя версия пакета описывала четыре режима:
- Study
- Practice
- Mock Interview
- Review

По мере уточнения доменной модели стало видно, что `Review` отличается
от остальных трёх сущностей по природе.

`Study`, `Practice` и `Mock Interview` меняют:
- цель сессии;
- форму ответа пользователя;
- hint policy;
- follow-up behavior;
- evaluation semantics;
- interpretation of collected evidence.

`Review` в основном обозначает:
- feedback artifact (`ReviewReport`);
- planning surface (`ReviewQueue`);
- remediation or spaced-review motivation for the next session.

Это не отдельная runtime family, а связка feedback + planning + recommendation intent.

## Decision

Зафиксировать:

1. В системе есть только три top-level runtime mode:
   - `Study`
   - `Practice`
   - `Mock Interview`
2. `Review` не является top-level mode.
3. Для planning и recommendation вводится отдельная ось `Session Intent`.
4. В v1 поддерживаются intents:
   - `LearnNew`
   - `Reinforce`
   - `Remediate`
   - `SpacedReview`
   - `ReadinessCheck`
5. Recommendation engine выбирает не только mode, но и intent.

## Consequences

### Positive
- runtime model становится чище;
- recommendation contract становится точнее;
- исчезает путаница между `ReviewReport`, `ReviewQueue` и `Review Mode`;
- remediation не порождает лишнюю ветку state machine.

### Trade-offs
- recommendation layer становится богаче;
- telemetry и session metadata теперь обязаны хранить `session_intent`;
- часть старых формулировок “review mode” надо заменить на review surface / remediation loop.

## Rejected alternative

Оставить `Review` как четвёртый mode.

Почему отклонено:
- он не задаёт самостоятельную форму runtime contract;
- он лучше моделируется как intent и planning surface;
- он плодит лишние special cases в runtime и analytics.
