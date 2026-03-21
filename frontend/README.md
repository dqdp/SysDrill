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

It does not implement learner dashboards, scenario/mock flows, or durable
cross-device resume.

## Persistence boundary

The shell currently stores:
- the active session envelope
- the shown launcher recommendation

This persistence is browser-local only and exists to make page refresh/reload
safe within the same browser profile. It is temporary implementation scaffolding
rather than a durable product contract: backend restarts, other browsers, and
other devices are not expected to recover this state.

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
