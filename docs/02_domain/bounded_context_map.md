# Bounded Context Map

## Overview

В системе выделяются шесть bounded contexts. Карта ниже фиксирует не только
области ответственности, но и **владельца смысла**: кто определяет доменную
истину, кто преобразует её в обучение, кто проводит сессию, кто оценивает,
кто строит learner state, и кто только отображает результат.

Главная цель этой карты — не дать системе выродиться в один LLM-blob,
где контент, педагогика, runtime, scoring и recommendation смешаны.

## Context 1. Content Kernel

### Responsibility
Канонический источник истины о знаниях по системному дизайну.

### Owns
- `Concept`
- `Pattern`
- `Scenario`
- `HintLadder`
- canonical explanations
- canonical axes and expected focus areas
- canonical follow-up candidates
- prerequisites and topic graph
- baseline content difficulty

### Does not own
- `Card` и другие учебные формы
- mode-specific hint policy
- session state и sequencing
- scoring decisions
- learner-specific recommendation

### Notes
Content Kernel отвечает на вопрос **"что считается канонически верным и
существенным в домене"**, но не на вопрос **"как именно это преподавать в
конкретном режиме"**.

## Context 2. Learning Design

### Responsibility
Преобразование knowledge objects в учебные формы и педагогические ходы.

### Owns
- `Card`
- `ExerciseTemplate`
- pedagogical goals
- mode-specific hint policy
- exercise difficulty transform
- sequencing metadata at design level
- transformation rules from knowledge objects to learning units
- follow-up envelope policy for each exercise type

### Does not own
- canonical truth of concepts or scenarios
- long-term learner personalization
- per-session turn state
- final evaluation result

### Notes
Learning Design отвечает на вопрос **"как преподавать"**: recall, compare,
trade-off drill, guided scenario, stricter mock. Он может менять форму
упражнения, но не канонический смысл доменного объекта.

## Context 3. Session Runtime

### Responsibility
Оркестрация конкретной учебной или интервью-сессии.

### Owns
- session state
- turn state
- delivery order within the session
- per-session follow-up selection
- hint requests and reveal control in-session
- completion / abandon transitions
- event emission

### Does not own
- canonical knowledge
- durable pedagogical templates
- long-term learner profile
- durable recommendation policy
- scoring semantics

### Notes
Runtime отвечает на вопрос **"что происходит сейчас в этой сессии"**.
Он не должен придумывать педагогику из сырого текста и не должен менять
канонический смысл задачи.

## Context 4. Evaluation Engine

### Responsibility
Оценка ответа пользователя в рамках завершённого turn или сессии.

### Owns
- rubric execution semantics
- criterion applicability at evaluation time
- criterion scores
- confidence computation
- evidence extraction rules
- gating failures
- evaluation result and review draft

### Does not own
- content truth
- learner trajectory planning
- UI rendering
- session sequencing

### Notes
Evaluation Engine отвечает на вопрос **"насколько хорошо пользователь покрыл
ожидаемые измерения ответа"**. Он использует rubric и scenario binding, но не
подменяет Content Kernel и не выбирает следующий шаг обучения.

## Context 5. Learning Intelligence

### Responsibility
Преобразование interaction history и evaluation outputs в learner model
и next-best-action recommendation.

### Owns
- append-only interaction log projection
- learner profile
- proficiency / confidence estimates
- retention risk
- review queue
- recommendation decisions and rationale
- anti-loop and fatigue-aware recommendation rules

### Does not own
- content truth
- session turn orchestration
- primary rubric scoring
- UI display logic

### Notes
Learning Intelligence отвечает на вопрос **"что делать дальше и почему"**.
Он не должен переписывать прошлую оценку и не должен жить внутри LLM
как неявная логика.

## Context 6. Interaction Layer

### Responsibility
Предъявление системы пользователю через web / text / later voice.

### Owns
- UI flows
- rendering of cards, prompts and reports
- client-side interaction collection
- accessibility and latency-sensitive interaction handling
- later STT/TTS adapters

### Does not own
- pedagogy semantics
- scoring semantics
- recommendation semantics
- canonical domain identifiers

### Notes
Interaction Layer отвечает на вопрос **"как это видит и трогает пользователь"**,
но не на вопрос **"что это значит в домене"**.

## Key boundaries

### Content Kernel -> Learning Design
Передаются нормализованные knowledge objects.
Learning Design может преобразовать их в разные учебные формы, но не может
молча менять канонический смысл, canonical axes или baseline difficulty.

### Learning Design -> Session Runtime
Передаются executable learning units.
Runtime не должен угадывать педагогику из сырого markdown и не должен
изобретать структуру упражнения во время сессии.

### Session Runtime -> Evaluation Engine
Передаются transcript, answer boundary, hint usage, timing и binding context.
Evaluation Engine возвращает оценку, но не редактирует transcript задним числом.

### Session Runtime + Evaluation -> Learning Intelligence
Передаются raw interaction events и evaluation outputs.
Learning Intelligence интерпретирует траекторию, но не вмешивается задним
числом в завершённый evaluation result.

### System -> Interaction Layer
UI получает уже интерпретированные доменные объекты: prompt, progress, review,
recommendation. Rendering не должно становиться владельцем смысла.

## Boundary tests

Система должна давать однозначный ответ на следующие вопросы:

1. Можно ли изменить `Card`, не меняя `Scenario`? — **Да**.
2. Можно ли изменить `canonical_axes` сценария, не меняя карточку? — **Да, но это
   content change, после которого Learning Design должен пересобрать учебные формы**.
3. Где живёт `guided recall` как артефакт? — **В Learning Design**.
4. Где живёт `baseline difficulty` сценария? — **В Content Kernel**.
5. Где живёт `strict mock difficulty` для того же сценария? — **В Learning Design / Runtime binding**.
6. Кто решает, какие follow-up реально показать в данной сессии? — **Session Runtime**,
   но только внутри envelope, полученного из Learning Design.

## Main anti-patterns

- Session Runtime напрямую меняет concept truth.
- LLM одновременно и teaching runtime, и evaluation source of truth,
  и recommendation engine без явных границ.
- `Card` хранится внутри `Scenario` как UI-поле, из-за чего pedagogy и content
  становятся неразделимыми.
- Recommendation опирается только на last score без полного interaction trail.
- UI компоненты становятся владельцем знания, rubric или recommendation logic.
