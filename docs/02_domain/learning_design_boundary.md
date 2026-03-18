# Learning Design Boundary

## Purpose

Этот документ фиксирует самую важную семантическую границу v1:
разделение между **Content Kernel** и **Learning Design**.

Без этой границы система почти неизбежно скатывается в один смешанный слой,
где knowledge objects, UI-компоненты, prompt text и pedagogical logic живут
вместе. Для учебного продукта это опасно: становится трудно развивать контент,
педагогику и runtime независимо.

## Boundary statement

- **Content Kernel** отвечает за то, что канонически верно и существенно в домене.
- **Learning Design** отвечает за то, как именно этот смысл превращается в обучение.
- **Session Runtime** отвечает за проведение конкретной сессии по уже заданной
  педагогической форме.

Иными словами:

- Content = **what is true and important**
- Learning Design = **how we teach it**
- Runtime = **how this specific session unfolds**

## Ownership matrix

| Artifact / field | Owner | Why |
|---|---|---|
| `Concept` | Content Kernel | Канонический доменный объект |
| `Pattern` | Content Kernel | Каноническое решение и его trade-offs |
| `Scenario.prompt` | Content Kernel | Задача как доменный объект |
| `Scenario.canonical_axes` | Content Kernel | Что важно покрыть по сути задачи |
| `Scenario.canonical_follow_up_candidates` | Content Kernel | Канонически уместные направления углубления |
| `Scenario.content_difficulty_baseline` | Content Kernel | Базовая сложность самой задачи |
| `HintLadder` | Content Kernel | Каноническая лестница раскрытия |
| `Card` | Learning Design | Учебная форма предъявления |
| `ExerciseTemplate` | Learning Design | Повторно используемая педагогическая форма |
| `pedagogical_goal` | Learning Design | Что именно мы тренируем |
| `difficulty_transform` | Learning Design | Как baseline difficulty меняется в этом типе упражнения |
| `hint_policy_ref` | Learning Design | Какие уровни hints допустимы в данном режиме |
| `follow_up_envelope` | Learning Design | Насколько глубоко можно идти в follow-ups |
| per-session follow-up selection | Session Runtime | Что реально показать именно сейчас |
| answer boundary | Session Runtime | Когда turn считается завершённым |

## What Content Kernel may change

Content change допускается, если меняется хотя бы один из следующих элементов:
- каноническое объяснение concept;
- список trade-offs;
- prerequisite relation;
- canonical axes scenario;
- canonical follow-up candidates;
- baseline difficulty;
- anti-shortcuts и common misconceptions.

После content change Learning Design обязан пересобрать затронутые учебные формы.

## What Learning Design may change without content change

Learning Design change допускается, если меняется хотя бы один из следующих элементов:
- превращение того же scenario в `mini_scenario` вместо `guided_compare`;
- prompt framing для recall / compare / trade-off drill;
- допустимые уровни hints;
- completion rules упражнения;
- difficulty transform для конкретного mode;
- sequencing metadata и pedagogical_goal.

Такие изменения не должны переписывать канонический смысл knowledge object.

## What Runtime may change without design change

Runtime change допускается, если меняется:
- конкретный order units внутри сессии;
- какой follow-up из envelope показан первым;
- когда остановить turn по времени или completion rule;
- какие raw events были эмитированы.

Runtime не должен:
- создавать новый pedagogical type on the fly;
- переписывать prompt semantics из design layer;
- менять baseline difficulty knowledge object.

## Transformation pipeline

Правильная цепочка выглядит так:

1. `Scenario` / `Concept` / `Pattern` существуют в Content Kernel.
2. Learning Design применяет `Card` или `ExerciseTemplate`.
3. Получается `ExecutableLearningUnit` для конкретного mode.
4. Session Runtime проводит конкретную сессию по этой единице.
5. Evaluation и Learning Intelligence работают уже на результате исполнения.

Неправильная цепочка выглядит так:

1. Runtime берёт сырой markdown.
2. LLM на лету придумывает упражнение, rubric и hint policy.
3. UI отображает то, что получилось.
4. Recommendation учится на непрозрачном артефакте.

## Design examples

### Example 1 — same scenario, different teaching forms

`Scenario: Design a URL Shortener`

Допустимые преобразования в Learning Design:
- recall card про `id_generation`;
- compare card: random ids vs counter-based ids;
- guided mini-scenario для read-heavy workload;
- strict mock prompt без hints.

Это разные учебные формы одного и того же knowledge object.

### Example 2 — changing canonical axes

Если для `chat system` добавляется новый canonical axis
`offline delivery guarantees`, это **content change**.
Даже если prompt в UI визуально не меняется, Learning Design обязан
пересобрать relevant cards, templates и scenario bindings.

### Example 3 — changing strictness

Если для `Practice Mode` мы решаем ограничить hints до уровней 1–2,
это **Learning Design change**, а не content change.

## Boundary tests

Следующие вопросы должны иметь однозначный ответ:

1. Можно ли переписать карточку так, чтобы она лучше учила comparison,
   не трогая canonical scenario? — **Да**.
2. Можно ли удалить `canonical_axes` у scenario, потому что evaluator и так
   знает, что проверять? — **Нет**.
3. Можно ли хранить `Card.prompt` внутри `Scenario`? — **Нет**, это смешивает
   content и pedagogy.
4. Можно ли делать mode-specific difficulty (`strict_mock`) полем scenario? — **Нет**,
   это обязанность Learning Design.
5. Можно ли разрешить Runtime генерировать follow-up без envelope? — **Нет**,
   иначе session orchestration начинает незаметно владеть педагогикой.

## Consequences for repository structure

Из этой границы следуют три правила для repo:

1. Контентные файлы и учебные шаблоны должны лежать раздельно.
2. Изменения в content должны быть видны как content diff, а не как prompt tweak.
3. Review и recommendation не должны ссылаться на UI labels как на source of truth;
   они должны ссылаться на stable domain ids.


## Examples of learning-design card families

Learning Design may define several recurring card/exercise families over the same
content base, for example:

- `recall` — воспроизвести определение, use case, trade-offs;
- `comparison` — сравнить два решения или стратегии;
- `failure` — разобрать, где система ломается и что делать;
- `sequencing` — выстроить правильный interview reasoning order;
- `red_flag` — распознать поверхностный или interview-weak answer;
- `oral_variant` — та же учебная форма, но с акцентом на spoken articulation.

Это pedagogical transformations, а не новые knowledge objects.


## Operational separation in v1

The boundary between `Content Kernel` and `Learning Design` remains strict at the level of ownership, schema, and runtime responsibility.

v1 does **not** require a fully separate editorial workflow for those domains. Bundled topic packages are allowed as an authoring convenience, provided that canonical content sections and learning-design sections remain clearly distinguished.

This means the project allows:
- bundled topic authoring
- template-assisted derivation of learning units
- progressive enrichment over time

This does **not** allow:
- collapsing ownership
- mixing canonical truth with runtime orchestration rules
- requiring exhaustive exercise coverage for every concept at launch
