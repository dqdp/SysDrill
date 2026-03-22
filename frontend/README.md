# Frontend

This directory contains the thin TypeScript frontend shell for the current
reviewed prototype loop.

The frontend is intentionally kept outside the Python backend and tooling
packages so the interaction layer can evolve without changing the Python
workspace boundary.

## Scope

The current shell is intentionally narrow:
- request and display one backend recommendation
- load backend-provided manual launch options
- start a session over an existing `ExecutableLearningUnit`
- restore an in-flight session after a page reload using backend session truth
- submit one answer
- request evaluation
- display the resulting review
- run a bounded mock/readiness loop through `MockInterview / ReadinessCheck`
  with one backend-provided follow-up probe

It does not implement learner dashboards, richer multi-turn mock orchestration,
or durable cross-device resume.

## Persistence boundary

The shell currently stores:
- the active session envelope
- the shown launcher recommendation

This persistence is browser-local only and exists to make page refresh/reload
safe within the same browser profile. It is temporary implementation scaffolding
rather than a durable product contract: backend restarts, other browsers, and
other devices are not expected to recover this state.

## Mock boundary

The current mock support is intentionally bounded:
- the shell supports backend-driven `MockInterview / ReadinessCheck` sessions
- the backend owns scenario family, prompt, follow-up, evaluation, and review
  semantics
- the frontend should remain family-agnostic and render whichever bounded
  scenario family the backend exposes
- this is not a full interviewer UI or an open-ended multi-turn mock system

## Local run

1. Start the backend with a configured content export root.
2. Install frontend dependencies:
   `npm ci`
3. Start the frontend dev server:
   `npm run dev`

The dev server proxies `/content`, `/learner`, `/runtime`,
`/recommendations`, and `/health` to the local backend on
`http://127.0.0.1:8000`.

## Verification

- run unit/integration-style frontend tests:
  `npm run test:run`
- run the production build:
  `npm run build`
