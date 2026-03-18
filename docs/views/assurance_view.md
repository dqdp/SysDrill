# Assurance View

## Why assurance exists in this product

Продукт делает две чувствительные вещи:

1. обучает;
2. оценивает.

Поэтому необходимо сохранять проверяемость решений.

## Assurance objectives

- traceability of evaluation;
- traceability of recommendation;
- stable content provenance;
- explainability of major learning-path changes.

## Minimum evidence bundle per completed session

- session metadata
- content ids and content version
- user transcript
- hint usage
- rubric result
- review report
- learner profile update note
- recommendation decision id

## Questions an assurance reviewer must be able to answer

1. Какая версия сценария была показана?
2. Какие критерии оценки применялись?
3. Почему recommendation engine предложил именно этот шаг?
4. Можно ли восстановить контекст сессии без неявных допущений?
5. Не превратилась ли система в black box?

## Assurance boundary

Ассюрэнс не требует математического доказательства всего.
Но он требует, чтобы значимые выводы системы были
**достаточно восстановимы и объяснимы**.
