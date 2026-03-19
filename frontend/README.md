# Frontend

This directory contains the thin TypeScript frontend shell for the current
manual reviewed prototype loop.

The frontend is intentionally kept outside the Python backend and tooling
packages so the interaction layer can evolve without changing the Python
workspace boundary.

## Scope

The current shell is intentionally narrow:
- load backend-provided manual launch options
- start a session over an existing `ExecutableLearningUnit`
- submit one answer
- request evaluation
- display the resulting review

It does not implement recommendation, learner dashboards, or scenario/mock
flows.

## Local run

1. Start the backend with a configured content export root.
2. Install frontend dependencies:
   `npm ci`
3. Start the frontend dev server:
   `npm run dev`

The dev server proxies `/content`, `/runtime`, and `/health` to the local
backend on `http://127.0.0.1:8000`.

## Verification

- run unit/integration-style frontend tests:
  `npm run test:run`
- run the production build:
  `npm run build`
