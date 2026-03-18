# Product Mission and Scope

## Mission

Построить платформу, которая превращает reference-знания по системному дизайну
в **активную тренировку**: recall, reasoning, trade-offs, scenario practice,
mock interview и объяснимую обратную связь.

Продукт должен переводить пользователя из состояния “читал и узнавал”
в состояние “могу вспомнить, структурировать и защитить решение”.

## Problem statement

У инженеров есть доступ к хорошим reference-материалам, но не хватает системы,
которая:

- заставляет воспроизводить знания без подсказки;
- помогает переносить концепты в реальные design scenarios;
- тренирует не только понимание, но и articulation under follow-up pressure;
- показывает, что именно в ответе было сильным или слабым;
- подстраивает следующий шаг обучения по истории взаимодействий.

## Primary outcomes

Пользователь должен:

1. чаще отвечать без раскрытия готового ответа;
2. лучше структурировать решение системной задачи;
3. реже пропускать требования, ограничения и failure modes;
4. увереннее проговаривать trade-offs;
5. проходить из study mode в mock interview не “случайно”, а по готовности.


## Product positioning

System Design Trainer — это **не банк вопросов и не пассивная библиотека материалов**.
Это тренажёр мышления под интервью: продукт, который учит вспоминать,
структурировать, проговаривать и защищать системное решение.

## User-facing learning journey

На product surface progression объясняется так:

1. изучил тему;
2. потренировал recall;
3. прошёл guided practice;
4. сделал mini mock;
5. дошёл до full mock.

Эта формулировка не подменяет domain-level modes model, а служит user-facing
объяснением того, как продукт ведёт пользователя от знания к interview fluency.

## Target users

### Primary
Инженер, готовящийся к system design interview.

### Secondary
Инженер middle/senior уровня, которому нужен регулярный тренажёр архитектурного мышления.

### Future
Команды и лиды, использующие продукт как internal training surface.

## v1 scope

В v1 поставляются:

- нормализованный knowledge core;
- текстовый Study Mode;
- текстовый Practice Mode;
- текстовый Mock Interview Mode;
- rubric-driven review surfaces и remediation loops;
- learner profile и recommendation engine v1;
- event logging и базовая аналитика;
- practical MVP content bootstrap: 50–100 качественных карточек по базовым темам;
- 3–5 mini-mock scenarios для проверки progression loop.

## Non-goals for v1

В v1 не входят:

- real-time voice-first UX;
- diagram editor;
- fully autonomous curriculum generator;
- marketplace of custom scenarios;
- interviewer marketplace / social features;
- advanced cohort analytics for B2B.

## Success criteria

### User success
- рост quality rubric score по повторным сессиям;
- снижение hint dependency;
- увеличение completion rate scenario sessions;
- явная weak-area remediation.

### Product success
- retention после первых 3 сессий;
- повторяемость weekly practice;
- завершение mock interview без perceived randomness;
- положительная оценка usefulness of feedback.

## Scope control questions

Любая новая фича должна проходить через вопросы:

1. Улучшает ли она skill acquisition, а не только UX?
2. Можно ли её объяснить через существующие bounded contexts?
3. Не пытается ли она подменить knowledge model магией LLM?
4. Не разрушает ли она explainability learning track?
5. Нужна ли она до доказательства текстового core loop?
