# Personas and Skill Model

## Persona 1 — Interview Candidate

### Motivation
Подготовка к системному дизайну на собеседования senior / staff track.

### Pain points
- знает термины, но не может собрать ответ под ограничением времени;
- пропускает важные ограничения;
- не умеет структурировать ответ как интервьюер ожидает;
- не видит свои слабые места системно.

### Desired outcome
Пройти путь от “читал материалы” к “могу уверенно разобрать сценарий”.

## Persona 2 — Practicing Engineer

### Motivation
Поддерживать архитектурное мышление в тонусе.

### Pain points
- редко тренирует системный дизайн явно;
- забывает редкие, но важные аспекты;
- хочет короткие, но плотные сессии.

## Skill model

Система тренирует не один “общий уровень”, а несколько subskills.

### 1. Requirement discovery
Умение извлекать функциональные и нефункциональные требования.

### 2. Constraint framing
Умение выделять нагрузку, latency, consistency, cost, durability, abuse vectors.

### 3. System decomposition
Умение разбивать систему на осмысленные компоненты и потоки.

### 4. Data modeling and storage choice
Умение выбирать storage и объяснять последствия выбора.

### 5. Scaling strategy
Умение выявлять bottlenecks и точки масштабирования.

### 6. Reliability and operations
Умение обсуждать retries, failure modes, monitoring, recovery.

### 7. Trade-off articulation
Умение сравнивать варианты, а не только перечислять компоненты.

### 8. Communication clarity
Умение вести ответ последовательно и interview-ready.

### 9. Structured articulation
Умение объяснять решение вслух или в длинном ответе так, чтобы собеседник
понимал порядок мыслей, переходы между уровнями системы и границы неопределённости.

### 10. Answer defense under follow-up pressure
Умение не просто дать стартовый ответ, а удерживать reasoning, уточнять assumptions
и защищать выбор под follow-up questions.

## Proficiency ladder

### L0 — Recognition
Пользователь узнаёт термин, но не объясняет его уверенно.

### L1 — Guided recall
Пользователь воспроизводит идею с небольшой подсказкой.

### L2 — Independent recall
Пользователь объясняет концепт без подсказки.

### L3 — Applied reasoning
Пользователь использует концепт в mini-scenario.

### L4 — Scenario synthesis
Пользователь интегрирует несколько концептов в задаче.

### L5 — Interview fluency
Пользователь держит связный дизайн-диалог под follow-up pressure.

## Implication for recommendation

Recommendation engine обязан выбирать не только **что учить**,
но и **в каком режиме тренировать этот subskill**:

- recall;
- compare;
- trade-off drill;
- mini-scenario;
- strict interview turn;
- oral rehearsal where applicable.

## What the learner model should estimate

Минимальный набор оценок:

- concept mastery;
- subskill mastery;
- hint dependency;
- forgetting risk;
- scenario transfer ability;
- mock interview readiness;
- structured articulation readiness;
- answer-defense readiness under follow-up pressure.


## Learner-state interpretation note

Внутренняя learner model v1 не утверждает абсолютное `mastery`.
Для concepts, subskills и mock-readiness система хранит `proficiency_estimate + confidence`.
Это позволяет различать подтверждённую слабость, подтверждённую силу и недостаток evidence.
