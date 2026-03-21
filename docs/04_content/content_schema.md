# Content Schema

## Objective

Контент должен быть нормализованным и переиспользуемым. Он не должен жить
только как сырой prompt text или UI-компонент. Этот документ описывает именно
**Content Kernel schema**.

`Card`, `ExerciseTemplate` и mode-specific units в эту схему не входят:
они принадлежат Learning Design.

## Entity: Concept

### Required
- `id`
- `title`
- `description`
- `why_it_matters`
- `when_to_use`
- `tradeoffs`
- `related_concepts`
- `prerequisites`

### Optional
- `examples`
- `anti_patterns`
- `common_misconceptions`
- `references`

## Entity: Pattern

### Required
- `id`
- `name`
- `problem_it_solves`
- `typical_components`
- `strengths`
- `weaknesses`
- `failure_modes`
- `related_concepts`

### Optional
- `references`
- `anti_patterns`

## Entity: Scenario

### Required
- `id`
- `title`
- `prompt`
- `content_difficulty_baseline`
- `expected_focus_areas`
- `canonical_axes`
- `canonical_follow_up_candidates`

### Optional
- `hidden_constraints`
- `anti_shortcuts`
- `reference_patterns`
- `bound_concept_ids`
- `references`

### Notes
- `content_difficulty_baseline` — это базовая сложность самой задачи,
  а не mode-specific strictness.
- `canonical_follow_up_candidates` — канонически уместные направления углубления,
  а не session-specific queue вопросов.
- `bound_concept_ids` — явная canonical привязка scenario к concept ids, которые
  могут использоваться для conservative post-mock targeting и learner-state
  updates. Это не runtime queue и не эвристика по `expected_focus_areas`.

## Entity: HintLadder

### Required
- `id`
- `content_id`
- `levels`

### Optional
- `disclosure_policy_note`

### Rules
- hint levels must progress from low disclosure to high disclosure;
- earlier levels should preserve learner effort;
- later levels may become increasingly concrete, but should not rewrite
  the whole answer unless explicitly marked as reveal.

## Out of scope for Content Schema

Следующие сущности **не входят** в Content Kernel schema:
- `Card`
- `ExerciseTemplate`
- `ExecutableLearningUnit`
- session state
- rubric execution outputs
- learner profile
- recommendation decisions

## Authoring rules

1. Один concept — один primary record.
2. Trade-offs должны быть явными, а не подразумеваемыми.
3. Scenario должен явно указывать canonical axes.
4. Baseline difficulty фиксирует сложность knowledge object,
   а не UI-режима.
5. Canonical follow-up candidates описывают существенные направления углубления,
   но не задают конкретный runtime order.
6. Hint ladder должен сохранять learner effort как можно дольше.
7. Content authoring должно оставаться отдельным от pedagogical templating и UI layout.

## Minimal v1 content pack

### Concepts
- caching
- replication
- sharding
- load balancing
- indexing
- queues
- pub/sub
- rate limiting
- CDN
- consistency basics
- storage choices
- id generation

### Scenarios
- URL shortener
- rate limiter
- chat system
- notification system
- news feed
- media/file delivery


## Relationship to Learning Design

Из объектов этого schema Learning Design может производить разные учебные формы:
recall, comparison, failure, sequencing, red-flag and oral variants.
Эти формы не входят в Content Kernel, но schema должен быть достаточно богатым,
чтобы поддерживать их без копирования знания в UI-specific prompts.


## Coverage model for v1

The v1 content model uses **progressive coverage**.

Required:
- canonical content must be present for launch-worthy topics
- at least one usable learning path into `Study` or `Practice` should exist for launch-worthy topics

Optional:
- not every topic must provide every supported card type
- not every concept must immediately map to a scenario
- not every topic needs oral-capable variants or enriched remediation metadata at launch

The schema should therefore distinguish between:
- required canonical fields
- optional canonical support fields
- optional learning-design derivatives

Template-assisted derivation is preferred where it reduces authoring burden without weakening schema clarity.
