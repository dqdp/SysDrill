# Slice 012: Learner Summary Surfaces

## Status

- completed

## Execution posture

`012` should begin only after `011` lands its runtime/event seams so learner
summary surfaces can consume real support/abandonment/closure facts rather than
permanent bootstrap zero baselines.

## Goal

Expose the first learner-facing summary surface for the internal
`learner_projection` and projector-backed recommendation loop, without freezing
the entire internal learner-profile shape as a public API contract.

This slice exists to make the intelligence introduced in `009` and `010`
visible and explainable to the learner by showing:
- weak or fragile areas
- review-due targets
- conservative readiness summary
- recommendation rationale grounded in learner-state summaries

## Affected bounded contexts

- `web_api / ui`
- narrow read surface over `learner_projection`
- narrow read surface over `recommendation_engine`

## Non-goals

- no full analytics dashboard
- no editable learner model
- no new recommendation action families
- no raw learner-profile dump as a frozen public contract
- no cohort/team analytics
- no new persistence layer
- no `current_stage` surface while its semantics remain undefined

## Constraints

- preserve v2.2 baseline and current bounded-context ownership
- recommendation remains the selector of structured learning actions
- UI must not invent learner semantics client-side
- empty or sparse evidence must render as unknown/insufficient evidence, not
  confirmed weakness
- readiness language must remain conservative and honest about evidence quality
- the internal `LearnerProfile` shape may continue evolving after `012`

## Known starting point

- `009` introduced an internal `LearnerProjector` with concept, partial
  subskill, and trajectory state
- `010` made recommendation consume learner projection internally
- there is currently no learner-facing read endpoint or UI summary for this
  state
- current frontend shell already supports recommendation launcher, active
  session, review, and basic recovery flows
- `current_stage` is intentionally omitted from projector output today

## Architectural approaches considered

### Option A: Summary-shaped API and UI

- add a narrow backend summary endpoint or equivalent read surface that returns
  learner-facing summaries rather than the raw internal profile
- render those summaries in the current launcher/review shell

Trade-offs:
- best fit for scope and contract discipline
- keeps internal learner-profile evolution flexible
- requires explicit summary mapping on the backend

### Option B: Raw profile passthrough to UI

- expose the internal learner profile directly and let the frontend decide what
  to show

Trade-offs:
- fastest path in terms of code volume
- freezes a premature backend shape into a UI dependency
- pushes learner semantics into the client
- higher long-term contract cleanup cost

### Option C: Recommendation-rationale only

- show only recommendation rationale and skip dedicated learner summaries

Trade-offs:
- smallest visible surface
- under-delivers on the user-visible value of `009`
- keeps weak-area/readiness loops mostly opaque

Decision:
- choose Option A

## Proposed implementation shape

### Backend summary contract

Add a narrow learner-summary read surface owned by `web_api / ui` and backed by
`learner_projection`.

Recommended summary sections:
- `weak_areas`
- `review_due`
- `readiness_summary`
- `evidence_posture`

Rules:
- response should be summary-shaped and learner-facing, not a raw serialization
  of the entire projector output
- every surfaced item should be traceable to current projector fields or current
  recommendation rationale
- unknown or unsupported areas should be omitted or labeled as insufficient
  evidence rather than rendered as weak

Recommended response posture:
- `weak_areas`: ordered list, maximum 3 items
- `review_due`: ordered list, maximum 3 items
- `readiness_summary`: single summary object
- `evidence_posture`: short list or object explaining current uncertainty

Rules:
- prefer labels, categories, and short explanations over raw numeric dumps
- include canonical target identifiers only where the UI needs stable linking
- do not expose the entire internal `LearnerProfile` as an accidental shadow
  contract

### Recommendation explanation bridge

Expose enough learner-facing rationale so the UI can show why the current
recommendation was chosen.

Rules:
- learner-summary read surface owns learner-state summary
- recommendation response owns decision-specific explanation for "why this
  action now"
- rationale should reference learner-state facts already used by recommendation
- UI should not reconstruct rationale heuristically from raw metrics
- if the current recommendation surface is too thin, use additive
  recommendation-response fields rather than duplicating decision semantics in
  the summary endpoint

### UI surface shape

Use the existing launcher/review shell as the first rendering surface.

Expected UI behaviors:
- launcher shows current summary cards or panels
- summary remains coherent after review completion and reload
- empty state explicitly communicates insufficient evidence
- recommendation CTA stays primary; summary is contextual support, not a second
  decision engine

Error/degraded-mode rules:
- summary load failure must not block launcher or recommendation usage
- UI may render a degraded launcher without summary, but must not invent or
  cache synthetic learner conclusions client-side
- stale summary data must be discarded rather than presented as current truth

## Summary scope for 012

### Weak areas

Surface only evidenced weak or fragile areas that the current projector can
support honestly:
- concept targets with low proficiency and sufficient confidence
- supported subskills with weak enough evidence to matter

Rules:
- sparse evidence does not become a weak-area label
- unsupported subskills stay absent
- weak areas should be ordered by backend-owned severity/importance, not by
  frontend heuristics

### Review-due

Surface targets whose projected `review_due_risk` is high enough to be useful.

Rules:
- review due should align with recommendation maintenance/remediation posture
- the surface should prefer a small, interpretable set over an exhaustive dump
- review-due ordering should be backend-owned and deterministic

### Readiness summary

Show a conservative readiness summary derived from `trajectory_state`.

Rules:
- language must communicate uncertainty where confidence is low
- if mock-readiness confidence is insufficient, say so directly
- do not imply formal stage progression while `current_stage` remains undefined
- readiness summary should be categorical first and only secondarily metric-like

### Evidence posture

If needed, include a small summary of why the system is uncertain:
- limited practice evidence
- support-dependent recent work
- insufficient repeated evidence

Rules:
- evidence posture is explanatory, not punitive
- it should help the learner understand why the system is recommending more
  practice or review
- evidence posture must not duplicate the full recommendation rationale

## Test contract

### 1. Empty learner state renders as unknown, not weak

Given:
- no reviewed evidence for the learner

Then:
- summary surfaces show insufficient evidence or an equivalent neutral empty
  state
- weak-area sections are absent or empty
- recommendation context remains coherent with the empty summary

### 2. Weak concept evidence appears consistently

Given:
- a learner profile with a confirmed weak concept target

Then:
- summary surfaces show that target as a weak area
- recommendation rationale can point to the same target without contradiction

### 3. Fragile success drives review-due summary

Given:
- recent support-dependent or fragile success with elevated review-due risk

Then:
- summary surfaces include the target in `review_due`
- the surface does not overstate it as a fully weak concept if the profile says
  it is fragile rather than weak

### 4. Stable evidence suppresses false weakness

Given:
- stable positive evidence for a concept

Then:
- summary surfaces do not show that concept as weak
- recommendation and summary stay aligned on maintenance posture

### 5. Unsupported subskills stay absent

Given:
- projector output with no evidence for unsupported v1 subskills

Then:
- UI does not render synthetic weakness for those subskills

### 6. Readiness summary stays conservative

Given:
- only limited concept-recall history with low mock-readiness confidence

Then:
- readiness summary communicates uncertainty explicitly
- UI does not imply the learner is fully ready for a mock by default

### 7. Summary survives launcher/review flows

Given:
- current frontend launcher and review shells with persisted reload/recovery

Then:
- summary loads deterministically on initial launcher render
- summary still renders coherently after session completion/reload
- UI does not invent client-side learner state if backend data is missing

### 8. Summary failure degrades safely

Given:
- summary fetch failure while recommendation and launcher APIs remain healthy

Then:
- launcher remains usable
- learner summary is omitted or shown as unavailable
- UI does not render stale or client-invented weak/readiness claims

## Acceptance criteria

- there is a narrow learner-facing summary read surface
- UI renders weak-area, review-due, and readiness summaries without exposing a
  raw internal learner-profile dump
- ownership between learner-summary data and decision-specific recommendation
  explanation is explicit
- empty state is explicitly neutral rather than punitive
- recommendation rationale and learner summary stay semantically aligned
- unsupported or low-confidence signals are presented honestly
- degraded summary loading does not block recommendation usage

## Weak spots review

- a summary contract can still become sticky if too many raw numeric details are
  exposed
- readiness is easy to over-message given the still-conservative evidence base
- if recommendation rationale fields are too implicit, the UI may be tempted to
  reverse-engineer backend logic locally
- summary ordering and density can create UX noise if every weak/review-due item
  is shown at once
- if summary cardinality is not capped, the launcher can devolve into a noisy
  pseudo-dashboard too early

## Hidden assumptions called out

- the launcher/review shell is a sufficient first home for learner summaries;
  a separate dashboard is not required yet
- additive explanation fields on recommendation responses remain acceptable if
  the current response shape is too thin, but decision-specific explanation
  should still stay owned by recommendation rather than the summary endpoint
- the current internal projector output is stable enough to support a summary
  mapping layer even if it is not yet suitable as a public contract

## Source-of-truth review

- `docs/00_change_protocol.md`: learner-state and recommendation sync set may
  matter if public surfaces change materially
- `docs/03_architecture/learner_state_update_rules_v1.md`: summary semantics
  must stay faithful to learner-state rules
- `docs/03_architecture/recommendation_policy_v1.md`: surfaced rationale should
  align with policy posture
- `docs/03_architecture/recommendation_engine_surface.md`: check whether
  additive rationale fields require documentation updates
- `docs/03_architecture/implementation_mapping_v1.md`: dashboard/summary
  surfaces belong to `web_api / ui`

## Change protocol expectations

- no ADR expected if `012` adds only narrow learner-facing read surfaces that
  preserve current ownership
- source-of-truth doc updates may be required if a new learner-summary API
  contract becomes load-bearing
- v2.2 baseline should remain preserved
