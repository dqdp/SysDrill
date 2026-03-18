# Concept Recall Binding v1

## Purpose

This document defines the first bounded non-scenario evaluation binding used by
the manual prototype path.

It exists so the initial deterministic review loop can score the currently
materialized `concept_recall` executable unit family without pretending that
scenario-family bindings already cover this path.

## Binding model

This binding defines:
- `binding_id`
- `unit_family`
- `required_criteria`
- `secondary_criteria`
- `criterion_weights`
- `gating_conditions`
- `mode_adjustments`
- `expected_evidence_cues`

## Binding id

`binding.concept_recall.v1`

## Unit family

`concept_recall`

## Required criteria

- `concept_explanation`
- `usage_judgment`
- `trade_off_articulation`

## Secondary criteria

- `communication_clarity`

## Weights

- `concept_explanation`: `1.3`
- `usage_judgment`: `1.1`
- `trade_off_articulation`: `1.0`
- `communication_clarity`: `0.7`

## Gating conditions

Hard failure if either is true:
- the transcript is empty after normalization
- the answer misses all three primary dimensions:
  - what the concept is
  - when to use it
  - the main trade-offs

## Mode adjustments

### Study
- formative posture
- no pass/fail threshold
- weighted score is reported without extra strictness penalty

### Practice
- stricter posture than `Study`
- incomplete coverage lowers the aggregate score more aggressively
- guidance threshold for this prototype path:
  - no hard gating failure
  - weighted score should be directionally above `0.50`

### MockInterview
- not supported by this binding in the current prototype path

## Expected evidence cues

- explanation-like wording that defines the concept in working terms
- usage-fit cues that explain when the concept is appropriate
- downside or cost cues that surface trade-offs
- enough answer structure to judge communication clarity conservatively

## Review posture

Review output for this binding should remain deterministic and compact.

It should include:
- strengths
- missed dimensions
- shallow areas
- next-focus suggestion
- support-dependence note where relevant

## Notes

- this is a bounded prototype binding, not a replacement for
  `scenario_rubric_binding_v1.md`
- it preserves rubric-first posture by using criteria from the global rubric
  schema rather than free-form scoring
