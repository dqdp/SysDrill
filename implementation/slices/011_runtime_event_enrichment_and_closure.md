# Slice 011: Runtime Event Enrichment And Closure

## Status

- completed

## Execution posture

Implementation order for this slice:
- add runtime/service tests first for completion, abandonment, hint, and reveal
- add API tests for the new runtime hooks
- wire the current frontend shell so explicit launcher exit and review exit map
  cleanly to completion/abandonment semantics
- update `learner_projection` and recommendation-consumption tests only after
  runtime event emission is stable

## Goal

Bring the implemented `session_runtime` closer to the binding v1 runtime/event
contracts so downstream learner and recommendation logic can consume real
support, closure, and abandonment signals instead of bootstrap zero baselines.

This slice exists to close the current gap between:
- the documented event/state-machine contracts in
  `interaction_event_model.md` and `session_runtime_state_machine_v1.md`
- the currently implemented runtime path that mostly stops at
  `review_presented`
- the dormant learner/recommendation signals introduced in `009` and `010`

## Affected bounded contexts

- `session_runtime`
- narrow consumption in `learner_projection`
- narrow consumption in `recommendation_engine`
- minimal `web_api / ui` hooks only where needed to exercise runtime transitions

## Non-goals

- no new recommendation policy family
- no learner dashboard work
- no full follow-up-round orchestration yet
- no mock-interview vertical slice yet
- no durable persistence redesign
- no event-streaming infrastructure
- no broad frontend redesign beyond the minimal controls needed to hit the new
  runtime transitions

## Constraints

- preserve v2.2 baseline and bounded-context ownership
- runtime remains the owner of session progression and semantic event emission
- runtime still must not mutate learner state directly
- emitted events remain semantic learning events, not raw UI exhaust
- new event handling must preserve append-only event discipline
- review retrieval must remain stable after completion
- abandonment must remain distinct from weak learner performance

## Known starting point

- current runtime already emits:
  - `session_planned`
  - `session_started`
  - `unit_presented`
  - `answer_submitted`
  - `evaluation_attached`
  - `review_presented`
  - `recommendation_accepted`
  - `recommendation_completed`
- current runtime does not yet emit the following documented load-bearing event
  families:
  - `session_completed`
  - `session_abandoned`
  - `hint_requested`
  - `answer_revealed`
- current frontend shell supports recommendation launch, answer submission,
  evaluation/review retrieval, reset/reload recovery, but not explicit session
  completion or support-use controls
- `009` currently keeps `recent_fatigue_signal`,
  `recent_abandonment_signal`, and support dependence mostly dormant because
  the needed runtime events do not exist yet

## Architectural approaches considered

### Option A: Narrow runtime-aligned enrichment

- implement only the missing runtime transitions/events already defined by the
  binding docs and needed by `learner_projection`
- keep the runtime public surface narrow
- add only minimal UI/API affordances required to exercise the transitions

Trade-offs:
- best fit for correctness and scope control
- unblocks richer learner signals without reopening architecture
- keeps `011` independent from `013` mock work
- still leaves follow-up events mostly dormant

### Option B: Broader runtime parity push

- implement closure, abandonment, hints, reveal, and first follow-up support in
  one slice

Trade-offs:
- closer to the full documented state machine
- higher product value per pass
- much greater scope and test surface
- higher risk of coupling `011` to mock/orchestration concerns that belong in
  `013`

### Option C: Projection-side inference only

- keep runtime as-is and infer completion, abandonment, or support dependence
  downstream from existing states

Trade-offs:
- smallest code delta
- violates semantic-event intent from the binding docs
- creates ambiguous, non-auditable learner evidence
- would hard-code projection heuristics around runtime omissions

Decision:
- choose Option A

## Proposed implementation shape

### Runtime transitions

Implement the narrow subset of documented transitions that unlock downstream
signals:
- `review_presented -> completed`
- allowed in-flight states -> `abandoned`
- repeatable support events from `awaiting_answer` and, if reachable in the
  current runtime, `follow_up_round`:
  - `hint_requested`
  - `answer_revealed`

Rules:
- `session_completed` is emitted exactly once per session
- `session_abandoned` is emitted exactly once per session
- support events do not change the top-level session state
- answer reveal does not mark a session completed or evaluated on its own

### Explicit state-transition matrix

`011` should lock the narrow allowed-state matrix up front.

Completion:
- allowed only from `review_presented`
- disallowed from every other state

Abandonment:
- allowed from:
  - `planned`
  - `started`
  - `unit_presented`
  - `awaiting_answer`
  - `follow_up_round` if that state is actually reachable
  - `submitted`
  - `evaluation_pending`
  - `evaluated`
- disallowed from:
  - `review_presented`
  - `completed`
  - `abandoned`

Support events:
- `hint_requested` allowed from `awaiting_answer` and from `follow_up_round`
  only if that state already exists in the active runtime path
- `answer_revealed` allowed only where unit policy explicitly permits it and
  the session is still answerable

### Event payload minimum contract

`011` should add enough payload detail for downstream auditability without
introducing UI exhaust.

Minimum payload expectations:
- `session_completed`:
  - `completed_from_state`
  - optional `session_duration_ms`
- `session_abandoned`:
  - `abandon_reason` (`explicit_exit`, `timeout`, or `runtime_interruption`)
  - `abandoned_from_state`
  - optional `session_duration_ms`
- `hint_requested`:
  - `hint_level`
  - `hint_count_for_unit`
  - optional `time_to_hint_ms`
  - optional `reason`
- `answer_revealed`:
  - `reveal_kind`
  - `reveal_count_for_unit`
  - `had_prior_hints`

Rules:
- payload contracts should stay additive and narrow
- payloads must support downstream learner interpretation without requiring the
  projector to inspect UI-local state
- if some fields are temporarily unavailable, the implementation should either
  synthesize them from runtime-owned facts or explicitly document the gap before
  landing code

### Minimal runtime/web seam additions

Expected narrow API/runtime hooks:
- a way to mark a reviewed session as closed/completed after the learner has
  seen the review
- a way to abandon/reset an in-flight session explicitly
- a way to request hint/reveal where the active unit policy allows it

Rules:
- these hooks should remain tightly scoped to the current text-first shell
- no new top-level mode or recommendation contract should be introduced

### UI and shell semantics mapping

To avoid noisy abandonment signals, `011` should explicitly map current shell
actions to runtime semantics.

Required mapping rules:
- explicit exit to launcher before stable closure maps to `abandoned`
- leaving the review screen after `review_presented` should first complete the
  session, then navigate away
- navigation/reload recovery failure by itself does not emit `abandoned`
- stale local resume cleanup does not emit `abandoned`
- generic launcher navigation after a session is already `completed` is a UI
  concern only and must not append new learner evidence

### Learner and recommendation consumption

Update downstream consumers narrowly:
- `learner_projection` should consume the new event families when present
- `recommendation_engine` may consume resulting trajectory/support signals, but
  no new policy family should be introduced in this slice

## Policy and semantic scope

### Completion semantics

`011` should operationalize the documented rule that a session is `completed`
only when the bounded action reaches a stable closure after evaluation/review
obligations are satisfied.

For the current prototype posture:
- review retrieval must continue to work after completion
- completion should be a post-review closure, not a replacement for review

### Abandonment semantics

`session_abandoned` should represent:
- explicit user exit before stable closure
- timeout or unrecoverable interruption when no complete reviewed outcome was
  produced

Rules:
- abandonment is a trajectory signal, not a direct concept-failure signal
- already reviewed/completed sessions should not be re-labeled abandoned

### Support-use semantics

`hint_requested` and `answer_revealed` should become first-class semantic facts.

Rules:
- `hint_requested` must record cumulative hint count and hint level when
  available
- `answer_revealed` remains a stronger dependency signal than hint use
- reveal/hint semantics belong to runtime/event facts; learner interpretation
  remains downstream

## Test contract

### 1. Completion event and stable retrieval

Given:
- a session that reached `review_presented`

Then:
- runtime can transition it to `completed`
- `session_completed` is emitted exactly once
- review retrieval still works after completion
- repeated completion calls do not double-emit or corrupt the session

### 2. Explicit abandonment from allowed states

Given:
- sessions in allowed pre-closure states such as `awaiting_answer`,
  `submitted`, `evaluation_pending`, or `evaluated`

Then:
- runtime can mark them `abandoned`
- `session_abandoned` is emitted exactly once
- later evaluation/review paths are blocked or handled deterministically

### 3. Launcher escape maps cleanly to abandonment

Given:
- the current frontend shell and an active non-closed session

Then:
- explicit user exit to launcher maps to runtime abandonment
- reload failure recovery or stale-local-state cleanup does not map to
  abandonment

### 4. No abandonment rewrite after closure

Given:
- a session already in `completed` or `review_presented` with stable closure

Then:
- abandonment does not rewrite that session history into an abandoned outcome

### 5. Hint requests are repeatable and state-preserving

Given:
- a session in `awaiting_answer`

Then:
- repeated hint requests emit `hint_requested`
- payload captures cumulative count/level where available
- top-level session state remains valid for continued answering

### 6. Answer reveal is distinct from hint use

Given:
- a unit policy that allows answer reveal

Then:
- runtime emits `answer_revealed`
- reveal does not masquerade as `unit_presented` or `hint_requested`
- later answer submission/evaluation remains deterministic if the learner
  continues

### 7. Event payloads are downstream-usable

Given:
- any newly emitted completion, abandonment, hint, or reveal event

Then:
- payload fields are sufficient for downstream learner interpretation
- the projector does not need UI-local context to distinguish support,
  closure, or abandonment meaning

### 8. Learner projection consumes new event families

Given:
- otherwise comparable reviewed histories with and without hint/reveal or
  abandonment facts

Then:
- support-dependent histories increase dependency signals and damp confidence
- abandonment histories raise `recent_abandonment_signal`
- absence of such events preserves prior bootstrap behavior

### 9. Recommendation remains stable under enriched events

Given:
- the same concept evidence with different recent support/abandonment history

Then:
- recommendation remains deterministic
- no public API shape changes occur
- trajectory/support signals may bias decisions without inventing new action
  families

## Acceptance criteria

- runtime emits `session_completed`, `session_abandoned`, `hint_requested`, and
  `answer_revealed` in the documented semantic places
- explicit completion and abandonment paths exist and are test-covered
- review retrieval remains stable after completion
- support-use events do not corrupt the current answer/evaluation flow
- `learner_projection` consumes the new events and stops holding relevant
  signals at permanent zero when evidence exists
- recommendation keeps its public surface and deterministic guardrails
- launcher/reset semantics do not pollute abandonment evidence

## Weak spots review

- completion UX can easily become ambiguous if the frontend also exposes a
  generic reset/launcher escape path that bypasses explicit closure
- abandonment semantics need a clear allowed-state boundary to avoid rewriting
  already-reviewed sessions
- hint/reveal payload detail may be partially synthetic until richer unit
  policies exist
- current UI reset semantics may need a small redesign so "discard local state"
  and "abandon active learning action" do not remain ambiguous
- adding follow-up events here would broaden the slice too far and should stay
  out unless implementation friction proves they are unavoidable

## Hidden assumptions called out

- a minimal explicit completion affordance can be added without revising mode or
  recommendation semantics
- support-use controls can be introduced in the current shell without turning
  UI exhaust into learner evidence
- the current evaluator/review flow can tolerate post-reveal submissions
  without needing a separate evaluation pathway

## Source-of-truth review

- `docs/00_change_protocol.md`: runtime flow and learner-evidence sync set must
  be checked during implementation
- `docs/03_architecture/interaction_event_model.md`: binding event semantics
- `docs/03_architecture/session_runtime_state_machine_v1.md`: binding state and
  transition posture
- `docs/03_architecture/learner_state_update_rules_v1.md`: downstream
  interpretation of support/abandonment evidence
- `docs/03_architecture/implementation_mapping_v1.md`: runtime ownership and
  anti-collapse rules

## Change protocol expectations

- no ADR expected if implementation simply closes the gap to existing binding
  docs
- source-of-truth doc updates may still be required if implementation reveals
  missing transition guards, payload fields, or closure semantics
- v2.2 baseline should remain preserved
