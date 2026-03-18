# Slice 005: Session Runtime And Event Log Bootstrap

## Status

- completed

## Goal

Create the first manual, bounded session-runtime path over materialized
`ExecutableLearningUnit` objects with append-only semantic event logging and an
explicit hand-off seam to evaluation.

## Why this is on the critical path

Milestone B requires a learner-visible loop as soon as possible:
- start one session manually
- present one bounded unit
- submit one answer
- capture semantic events
- hand off a stable answer boundary to evaluation

Without this slice, the backend still stops at content materialization and the
prototype cannot execute a learner session.

## In scope

- runtime bootstrap for a single-unit manual session
- minimal runtime/session models inside the backend
- append-only in-memory event log for prototype use
- explicit evaluation-request assembly after answer submission
- minimal backend API endpoints for manual session start, read, and answer
  submission
- deterministic state transitions for the bounded prototype path
- targeted backend tests for runtime transitions and event emission

## Out of scope

- recommendation-driven session start
- multi-unit session planning
- persistence beyond process-local in-memory stores
- hint request endpoints
- answer reveal endpoints
- follow-up round handling
- evaluation scoring and review generation
- learner-state projection
- frontend implementation

## Affected bounded contexts

- `Session Runtime`
- `Learning Design`
- `Evaluation Engine`
- `web_api / ui`

## Source-of-truth references

- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/02_domain/hand_off_contracts.md`
- `docs/02_domain/domain_model.md`
- `docs/03_architecture/session_runtime.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/03_architecture/evaluation_engine_v1.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `implementation/roadmap.md`
- `implementation/status.md`
- `implementation/slices/004_executable_learning_unit_materialization.md`

## Architectural options considered

### Option A: In-memory single-unit runtime bootstrap

- single bounded unit per session
- process-local in-memory session store
- process-local append-only event log
- explicit evaluation-request object assembled at submit time
- minimal HTTP endpoints for manual start and answer submission

Trade-offs:
- fastest path to a demoable prototype
- deterministic and easy to test
- volatile storage and intentionally narrow behavior

### Option B: Durable runtime bootstrap with broader state coverage

- file-backed or database-backed runtime persistence
- early support for hints, reveals, and follow-up rounds
- broader session orchestration from the start

Trade-offs:
- stronger operational posture
- slower path to first prototype
- higher risk of mixing runtime concerns with unfinished evaluation and
  recommendation work

Decision:
- choose Option A for this slice

## Proposed implementation shape

- add `backend/src/sysdrill_backend/session_runtime.py`
- add `backend/src/sysdrill_backend/session_runtime_api.py` only if the API
  wiring needs a thin adapter
- add `backend/tests/test_session_runtime.py`
- extend `backend/src/sysdrill_backend/app.py` with minimal runtime endpoints
- keep stores in memory and explicit; do not introduce a database yet

## Manual prototype posture

The first runtime bootstrap should support:
- manual selection of one materialized `ExecutableLearningUnit` by `unit_id`
- one active unit per session
- one answer submission path
- no recommendation dependency

The runtime should resolve the requested unit from materialized units for the
given `mode` and `session_intent`, not from raw topic-package content.

## Endpoint proposal

- `POST /runtime/sessions/manual-start`
- `GET /runtime/sessions/{session_id}`
- `POST /runtime/sessions/{session_id}/answer`

### `POST /runtime/sessions/manual-start`

Expected request:
- `user_id`
- `mode`
- `session_intent`
- `unit_id`
- optional `source` defaulting to `web`

Expected response:
- `session_id`
- `state`
- `mode`
- `session_intent`
- `current_unit`
- `planned_unit_ids`
- `event_ids`

### `POST /runtime/sessions/{session_id}/answer`

Expected request:
- `transcript`
- `response_modality`
- `submission_kind`
- optional coarse timing summaries such as `response_latency_ms`

Expected response:
- `session_id`
- `state`
- `submitted_unit_id`
- `evaluation_request`

## Local implementation contract

Because some runtime fields are named in docs but not fully schema-fixed, this
slice should use a narrow internal contract:

- session states used in this slice:
  - `planned`
  - `started`
  - `unit_presented`
  - `awaiting_answer`
  - `submitted`
  - `evaluation_pending`
- strictness profile values used in this slice:
  - `supportive` for `Study`
  - `standard` for `Practice`
- event-log store:
  - append-only list of full event records
  - no update/delete path

This contract is internal to the prototype bootstrap and not yet a public API
guarantee.

## Evaluation hand-off posture

This slice should not score answers yet.

Instead, it should assemble a deterministic `EvaluationRequest`-like payload
containing at least:
- `session_id`
- `session_mode`
- `session_intent`
- `executable_unit_id`
- `binding_id`
- `transcript_text`
- `hint_usage_summary`
- `answer_reveal_flag`
- `timing_summary`
- `completion_status`
- `strictness_profile`

The session should transition to `evaluation_pending` after a valid submission.

## Event-emission posture

For the manual bootstrap path, the runtime should emit in order:
- `session_planned`
- `session_started`
- `unit_presented`
- `answer_submitted`

This slice does not yet need `hint_requested`, `answer_revealed`,
`follow_up_presented`, or `follow_up_answered`.

## Test contract

- manual session start resolves a known `unit_id` and returns a session in
  `awaiting_answer`
- manual session start emits `session_planned`, `session_started`, and
  `unit_presented` in deterministic order
- started session stores the selected unit as the current and only planned unit
- `GET /runtime/sessions/{session_id}` returns the current session snapshot
- unknown `unit_id` fails closed with an explicit error
- mode/intent and unit-resolution mismatch fails closed with an explicit error
- answer submission from `awaiting_answer` transitions through `submitted` to
  `evaluation_pending`
- answer submission appends `answer_submitted` and never rewrites prior events
- answer submission assembles the expected evaluation hand-off payload
- repeated submission from an invalid state fails closed
- runtime event records contain required event-model fields
- runtime path does not mutate learner state and does not read raw exporter files

## Acceptance criteria

- backend can run one manual single-unit session over a materialized unit
- runtime emits append-only semantic events at the required boundaries
- answer submission produces an explicit evaluation hand-off payload
- runtime behavior remains deterministic and bounded
- no recommendation or learner-state logic is introduced
- the slice advances Milestone B directly

## Weak spots and assumption review

- hidden assumption: manual prototype launch is allowed before recommendation;
  this now matches the milestone plan and does not revise recommendation scope
- hidden assumption: process-local in-memory storage is acceptable for the first
  prototype loop; this is intentionally narrow and may be replaced later without
  changing runtime semantics
- weak spot: docs name `strictness_profile` but do not freeze its vocabulary;
  this slice should keep values local and minimal
- weak spot: the event model lists `session_planned`, while the runtime
  state-machine core transitions start at `planned -> started`; this slice should
  emit `session_planned` on creation and then continue through the state-machine
  path in the same request
- weak spot: evaluation docs mention `unit_family` / `scenario_family`; for this
  slice the hand-off should remain minimal and rely on the unit binding/id seam
  without widening domain contracts prematurely
- no contradiction found with v2.2 baseline, bounded-context ownership, or ADR
  decisions
- no ADR is required if this slice remains a prototype bootstrap and keeps
  storage/process choices local

## Verification

- targeted runtime unit/API tests
- `make verify-python`

## Definition of done

- explicit TDD tests exist for manual start, answer submission, and append-only
  event logging
- backend exposes the minimal runtime endpoints for a manual single-unit session
- runtime transitions reach `evaluation_pending` with an explicit hand-off
  payload
- roadmap/status remain synced
- the v2.2 implementation baseline remains preserved

## Outcome

- backend now supports manual single-unit session bootstrap over materialized
  `ExecutableLearningUnit` objects
- runtime emits append-only semantic events for session planning, start, unit
  presentation, and answer submission
- answer submission now produces an explicit evaluation hand-off payload and
  transitions the session to `evaluation_pending`
- implementation stays in-memory and prototype-scoped, without introducing
  recommendation, learner-state mutation, or scoring logic
