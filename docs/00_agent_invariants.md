# Agent Invariants

Implementation agents must not violate these invariants without an explicit new decision.

1. Do not collapse Content Kernel and Learning Design.
2. Do not collapse recommendation into Session Runtime.
3. Do not treat `Review` as a top-level runtime mode.
4. Do not replace rubric-first hybrid evaluation with pure free-form LLM scoring.
5. Do not treat low confidence as confirmed weakness.
6. Do not add low-level UI exhaust to learner evidence by default.
7. Do not make voice the v1 foundation.
8. Do not let recommendation control per-turn hint timing or follow-up sequencing.
9. Do not silently change schemas without updating examples and source-of-truth docs.
10. Do not bypass ADRs for load-bearing architectural decisions.
11. Do not widen recommendation beyond bounded structured actions.
12. Do not reopen frozen baseline decisions during normal implementation work; use ADR-backed revision only when real implementation evidence justifies it.
