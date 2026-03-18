# Product View

## What product is being built

System Design Trainer — это не библиотека материалов и не просто чат с AI.
Это продукт для **регулярной тренировки навыка системного дизайна**.

Его суть — помочь пользователю не просто узнать материал, а **вспоминать,
структурировать и защищать решение** в формате, приближенном к интервью.

## User promise

Пользователь получает:

- маленькие, но плотные тренировочные сессии;
- понятные слабые зоны;
- следующий шаг обучения, выбранный не случайно;
- mock interview, который ощущается как progression, а не как gimmick.

## Differentiation

Продукт позиционируется как **тренажёр мышления под интервью**, а не как
банк вопросов, пассивная библиотека материалов или generic flashcard app.

## User-facing progression

На уровне продукта progression объясняется так:

1. изучил тему;
2. потренировал recall;
3. прошёл guided practice;
4. сделал mini mock;
5. дошёл до full mock.

## AI tutor promise

ИИ приносит ценность не тем, что сразу пишет идеальный ответ, а тем, что он:

- не подсказывает слишком рано;
- оценивает по rubric;
- выявляет повторяющиеся пробелы;
- адаптирует сложность и следующий шаг;
- даёт post-interview feedback.

## Why the architecture matters to product

Если не отделить:
- knowledge,
- runtime,
- evaluation,
- recommendation,

то продукт быстро станет непредсказуемым:
одни и те же ответы будут оцениваться по-разному,
а персонализация будет казаться магией.

## Product moat hypothesis

Потенциальное преимущество продукта не только в UI и не только в LLM,
а в сочетании:

- нормализованного knowledge core;
- понятной pedagogy;
- explainable evaluation;
- durable learner model;
- recommendation loop.

## Product priorities for first release

1. сделать полезный текстовый core loop;
2. доказать ценность review artifacts + recommendation;
3. сделать mock interview как progression step;
4. не распыляться на voice-first и ornamental UX.
