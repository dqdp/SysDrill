# ADR-001: Normalized Knowledge Base as Source of Truth

Date: 2026-03-17  
Status: Accepted

## Context

Проект использует материалы по системному дизайну как reference base,
но продукт не должен зависеть от формы исходного материала или жить как набор prompt snippets.

## Decision

Канонический контент хранится как отдельная нормализованная knowledge base:
Concept / Pattern / Scenario / Hint Ladder / Rubric.

## Consequences

### Positive
- знания можно переиспользовать в разных режимах;
- UI не владеет смыслом;
- recommendation и evaluation работают поверх стабильных объектов.

### Negative
- нужна authoring discipline;
- выше начальные издержки на modeling.
