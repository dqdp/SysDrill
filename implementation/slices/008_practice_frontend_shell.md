# Slice 008: Practice Frontend Shell

## Status

- completed in current worktree

## Goal

Add a thin frontend or equivalent demo path that exercises the current verified
backend prototype loop end-to-end:
- choose a launchable unit
- start a manual session
- submit an answer
- attach evaluation
- display the resulting review

The purpose of this slice is demoability and contract validation, not UI polish
or expansion of domain scope.

## Why this is on the critical path

The backend prototype loop is now verified, but it still lacks a learner-visible
surface. Without this slice, the project remains backend-complete but not
demoable against the current milestone exit condition.

This slice should convert the verified manual reviewed loop into a visible,
bounded demo path without:
- introducing recommendation semantics early
- expanding scenario/mock scope
- moving domain logic into the UI

## In scope

- the first minimal TypeScript frontend application under `frontend/`
- a manual launcher UI for one bounded backend session path
- answer input and submit flow
- evaluate and review display flow
- narrow backend read support required to power the launcher honestly
- bounded frontend verification for the implemented shell

## Out of scope

- recommendation UI
- learner dashboard
- weak-area/readiness surfaces
- scenario-family and `MockInterview` frontend flows
- real authentication
- production design system work
- elaborate state management or routing architecture
- voice UX

## Affected bounded contexts

- `Interaction Layer`
- `web_api / ui`
- narrow backend read support around existing `Learning Design -> Runtime`
  seams

## Source-of-truth references

- `AGENTS.md`
- `docs/00_change_protocol.md`
- `docs/00_implementation_baseline_v2.2.md`
- `docs/02_domain/hand_off_contracts.md`
- `docs/03_architecture/implementation_mapping_v1.md`
- `docs/03_architecture/session_runtime_state_machine_v1.md`
- `docs/03_architecture/interaction_event_model.md`
- `docs/views/product_view.md`
- `docs/views/engineering_view.md`
- `implementation/roadmap.md`
- `implementation/status.md`
- `frontend/README.md`

## Architectural approaches considered

### Option A: Separate minimal TypeScript frontend plus narrow backend launcher endpoint

- create a small TypeScript frontend application in `frontend/`
- keep backend as the owner of launchable unit selection data
- add a narrow backend endpoint that lists launchable units for supported
  manual mode/intent combinations
- let the frontend only render and call APIs

Trade-offs:
- matches the documented repository direction and frontend boundary
- keeps `unit_id` derivation and runtime semantics out of the UI
- slightly wider than pure UI work because it needs one narrow backend surface

### Option B: Backend-served HTML demo surface

- add a simple backend-rendered page or static HTML under the Python app
- directly call existing backend runtime endpoints from the same app surface

Trade-offs:
- fastest visible demo
- avoids introducing frontend tooling immediately
- conflicts with the documented preference for a separate TypeScript frontend
- risks creating throwaway UI infrastructure that must be replaced immediately

Rejected because:
- it would save time now at the cost of violating the intended frontend
  boundary and increasing rewrite pressure

### Option C: Separate frontend that derives `unit_id` client-side from topic data

- build a TS frontend but avoid backend API changes by reconstructing unit IDs
  from `/content/topics` payloads

Trade-offs:
- seems small on paper
- pushes runtime launch semantics into the UI
- couples the UI to implementation details of `ExecutableLearningUnit` IDs

Rejected because:
- it violates the current ownership boundary and would make the UI invent
  runtime/business logic

Decision:
- choose Option A

## Proposed implementation shape

- initialize a minimal TypeScript frontend app in `frontend/`
- add a thin API client layer for the current backend endpoints
- add a backend endpoint that returns launchable units for manual demo use
- implement one screen or one small shell flow with four visible states:
  launcher, active prompt, evaluation-in-progress, review
- keep frontend state local and explicit; avoid introducing heavy client
  architecture in this slice

## Backend launcher contract proposal

The frontend should not derive or reconstruct `unit_id`.

Recommended backend read surface:
- `GET /runtime/manual-launch-options`

Required query params:
- `mode`
- `session_intent`

Recommended successful response shape:

```json
{
  "mode": "Study",
  "session_intent": "LearnNew",
  "items": [
    {
      "unit_id": "elu.concept_recall.study.learn_new.concept.alpha-topic",
      "content_id": "concept.alpha-topic",
      "topic_slug": "alpha-topic",
      "display_title": "Кэширование",
      "visible_prompt": "Explain the concept 'Кэширование'. Cover what it is, when to use it, and the main trade-offs.",
      "effective_difficulty": "introductory"
    }
  ]
}
```

Response-field rationale:
- `unit_id` is the only launch key the current runtime already accepts
- `content_id` preserves traceability to canonical content
- `topic_slug` and `display_title` give the UI a stable label without parsing
  prompt text
- `visible_prompt` is the preview of the actual launchable unit
- `effective_difficulty` is optional but useful for a minimal launcher surface

The endpoint should remain read-only and runtime-facing. It should not be folded
into `/content/topics` because launchability is not canonical content truth.

## Backend launcher error semantics

- `200` with `items=[]`:
  supported `mode/session_intent`, but no launchable units are currently
  available
- `400`:
  unsupported `mode/session_intent` combination
- `422`:
  malformed or missing query parameters
- `503`:
  runtime/content configuration is unavailable

The launcher endpoint should fail closed and should not silently coerce
unsupported combinations.

## Manual launcher posture

The launcher should remain honest to current implementation limits.

It should support only the already implemented prototype path:
- `Study`
- `Practice` only where a launchable supported unit exists
- manual start over existing materialized `concept_recall` units

It must not:
- invent recommendation actions
- infer hidden launch semantics from raw topic payloads
- pretend scenario or mock flows already exist

The launcher should use backend-provided launch options and then pass the chosen
`unit_id` unchanged into the existing manual-start runtime API.

## TDD plan

### Phase 1: backend launcher contract first

Add backend tests before frontend work if a new launcher endpoint is required.

Backend launcher contract:
- frontend can request launchable units from the backend for a supported
  `mode/session_intent`
- response includes stable `unit_id`, visible prompt preview, and source/topic
  context sufficient for manual selection
- unsupported `mode/session_intent` combinations fail closed
- supported combinations with no launchable units return an empty list rather
  than an error
- UI does not need to reconstruct `unit_id` locally

Implementation order inside Phase 1:
1. add backend service tests for launch-option listing
2. add backend API tests for the endpoint shape and errors
3. implement the runtime read method and API wiring
4. keep current smoke/backend loop green

### Phase 2: frontend shell contract tests

Add frontend-level tests for the minimal shell flow before implementation.

Frontend contract:
- launcher loads launchable unit options from the backend
- selecting a unit and starting a session transitions to the prompt view
- submitting an answer transitions to an evaluation state and then to review
- review view shows evaluation summary and review fields from the backend
- API failures are shown explicitly rather than silently ignored

### Phase 3: end-to-end demo verification

Add or update a bounded smoke path that proves the frontend shell can drive the
current backend loop.

Demo contract:
- one learner-visible path can start from launcher and end at review
- no recommendation dependency is required
- no real browser automation is required unless the frontend stack demands it

## Test contract

- frontend app installs and runs in a clean environment
- a bounded frontend verification command exists
- launcher endpoint returns only supported manual-launch units
- launcher endpoint returns deterministic ordering
- frontend does not hardcode or derive `unit_id` from raw content responses
- a learner can launch a manual session from the UI and reach review
- explicit error handling exists for backend failures or empty launcher state
- current backend smoke path remains green after frontend-related backend changes

## Acceptance criteria

- repository contains a minimal TypeScript frontend shell under `frontend/`
- the shell can drive the current manual reviewed backend loop from launcher to
  review
- the UI does not own recommendation or runtime derivation logic
- current backend verification remains green
- the slice delivers a demoable learner-visible prototype path

## Weak spots and assumption review

- hidden assumption: the frontend needs a backend-provided launcher surface
  because current APIs do not expose launchable `ExecutableLearningUnit` options
- hidden assumption: a dedicated launcher endpoint is safer than extending
  `/content/topics`, because launchability belongs to runtime-facing read
  semantics rather than canonical content
- hidden assumption: this slice should stay limited to the already-implemented
  `concept_recall` path and must not silently broaden product claims
- weak spot: if the frontend stack selection is too heavy, the slice may spend
  more effort on tooling than on the actual learner flow
- weak spot: if the backend launcher endpoint leaks too much implementation
  detail, the UI may accidentally become coupled to internal runtime structure
- weak spot: changing `manual-start` to accept logical targets instead of
  `unit_id` was considered but rejected for this slice because it would force
  early resolver semantics into runtime without a stable contract yet
- weak spot: browser-level e2e automation may be overkill for this slice if the
  shell is very thin; frontend verification should stay proportionate
- no contradiction found with the v2.2 documentation baseline if the UI remains
  a thin interaction layer over explicit backend contracts

## ADR check

No ADR is required if this slice:
- keeps the frontend as an interaction layer
- keeps recommendation out of the UI
- adds only a narrow backend launcher/read surface without changing bounded
  context ownership

## Verification

- run existing backend verification and smoke commands
- run the new frontend verification commands
- confirm a learner-visible flow reaches reviewed outcome against the backend

## Definition of done

- explicit slice-level TDD contract exists and is reviewed
- frontend shell exists and can drive the verified backend loop
- launcher data comes from the backend rather than frontend inference
- implementation docs remain in sync

## Review result

- recommended next step after this plan is implementation of the frontend shell
  itself, beginning with the narrow backend launcher contract
- concrete first implementation step:
  backend tests and endpoint for `GET /runtime/manual-launch-options`
- no conflicts found with `AGENTS.md`, the current ADR set, or the v2.2
  documentation baseline
