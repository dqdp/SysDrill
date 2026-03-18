# Evaluation Quality Plan v1

## Purpose
This document defines how evaluation quality is checked before widening scope or trusting scoring and review outputs operationally.

This document is specifically about **evaluation-subsystem quality assurance**.
It is not the general production metrics document.

## Quality goals
- similar answers receive acceptably similar scoring
- weak answers are identified for the right reasons
- support usage lowers independence confidence without collapsing all proficiency
- review outputs remain explainable and auditable
- scenario bindings are actually enforced
- evaluator/model changes do not silently shift scoring behavior

## Evaluation test corpus

### Golden answers
Strong, clearly acceptable answers for major scenario families and concept drills.

### Borderline answers
Partially correct answers with typical omissions.

### Weak answers
Answers that should clearly fail specific criteria.

### Adversarial vague answers
Verbose but shallow answers designed to expose false positives.

### Support-varied answers
Comparable answers with:
- no hints
- some hints
- reveal usage

Used to verify support-effect handling.

### Partial/abandoned answers
Incomplete transcripts used to check confidence degradation and conservative scoring.

## Required checks

### Consistency checks
- repeated scoring on the same answer stays within acceptable delta
- near-duplicate answers receive similar criterion results
- deterministic rule portions remain stable across reruns

### Criterion integrity checks
- observed evidence remains distinct from inferred judgment
- non-applicable criteria are not silently scored
- criterion confidence degrades when evidence quality degrades

### Support-effect checks
- hint-heavy success remains weaker evidence than independent success
- reveal usage increases support-needed interpretation
- support usage does not collapse all proficiency into failure

### Scenario-binding checks
- required criteria for each scenario family are actually enforced
- weighting and gating rules are applied as configured
- gating failures are surfaced in the final result

### Failure-mode checks
- partial transcripts do not receive high-confidence full coverage
- degraded evaluator/model paths are visible in output
- rubric/binding mismatch fails closed

## Release gates before widening scope
Before expanding content breadth or pushing voice deeper:
- no major consistency regressions
- no unresolved false-high scoring on adversarial vague answers
- no opaque criterion failures without evidence snippets
- no unacknowledged degraded mode in evaluation output
- no binding-enforcement regression on covered scenario families

## Regression policy
Run the quality corpus whenever:
- rubric schema changes
- scenario bindings change
- evaluation prompts or evaluators change
- evaluator/model version changes
- criterion aggregation logic changes
- downstream signal mapping changes materially

## Required audit payload
For every evaluated test item, preserve enough data to inspect:
- evaluation input summary
- rubric/binding version
- criterion results
- weighted score
- confidence note
- downstream signals
- review artifact
- evaluator/model version where applicable
- evaluation mode (`rule_only`, `llm_assisted`, `hybrid`)

## Operational stance
This quality plan should be treated as a release gate for evaluation changes, not as optional nice-to-have testing.
