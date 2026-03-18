# Session Runtime State Machine v1

## Purpose
This document defines the executable state-machine contract for Session Runtime. `session_runtime.md` explains the conceptual model; this file defines state transitions.

## Session states
- `planned`
- `started`
- `unit_presented`
- `awaiting_answer`
- `follow_up_round`
- `submitted`
- `evaluation_pending`
- `evaluated`
- `review_presented`
- `completed`
- `abandoned`

## Turn-level states
- `prompt_shown`
- `hint_requested` (repeatable)
- `answer_submitted`
- `follow_up_presented`
- `follow_up_answered`
- `turn_closed`

## Core transitions
### `planned -> started`
Trigger: learner accepts or starts a recommended action.
Emit: `session_started`

### `started -> unit_presented`
Trigger: runtime resolves the next `ExecutableLearningUnit`.
Emit: `unit_presented`

### `unit_presented -> awaiting_answer`
Trigger: learner-visible prompt shown.

### `awaiting_answer -> follow_up_round`
Trigger: runtime presents a follow-up within allowed envelope.
Emit: `follow_up_presented`

### `awaiting_answer -> submitted`
Trigger: stable answer boundary submitted.
Emit: `answer_submitted`

### `follow_up_round -> submitted`
Trigger: stable follow-up answer boundary submitted.
Emit: `follow_up_answered`, then `answer_submitted` for the turn outcome bundle if applicable.

### `submitted -> evaluation_pending`
Trigger: runtime hands off to evaluation.

### `evaluation_pending -> evaluated`
Trigger: evaluation result attached.
Emit: `evaluation_attached`

### `evaluated -> review_presented`
Trigger: review artifact shown.
Emit: `review_presented`

### `review_presented -> completed`
Trigger: session closure completes.
Emit: `session_completed`

### `* -> abandoned`
Trigger: explicit user exit, timeout, or unrecoverable flow interruption.
Emit: `session_abandoned`

## Optional transitions
### hint requests
Allowed from `awaiting_answer` or `follow_up_round`.
Emit: `hint_requested`
Do not change top-level session state.

### answer reveal
Allowed only where unit policy permits.
Emit: `answer_revealed`
Does not bypass later evaluation if learner continues, but lowers confidence in independent completion.

## Mode-specific notes
### Study
- hints and reveal commonly allowed
- shorter turns
- evaluation lighter

### Practice
- follow-up envelope moderate
- no unlimited scaffolding

### MockInterview
- stricter hint policy
- stronger follow-up pressure
- full review required before closure

## Completion semantics
A session is `completed` only when:
- the planned bounded action reached a stable closure, and
- evaluation/review obligations for that action were satisfied or intentionally skipped under explicit policy.

A session is `abandoned` when:
- the learner exits before stable closure, or
- runtime cannot produce a complete reviewed outcome.

## Invariants
- Session Runtime never mutates learner state directly.
- All meaningful boundaries emit semantic events.
- Partial transcripts must not be interpreted as full-confidence performance.
- Runtime may choose exact unit ordering, but may not violate recommendation action bounds.
