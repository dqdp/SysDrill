# System Design Trainer — Documentation Knowledge Base

This repository is the authoritative documentation bundle for **System Design Trainer** and is intended to serve as a knowledge base for implementation agents as well as humans.

**Status:** `v2.2` is the current **implementation baseline** for the first controlled implementation wave.

System Design Trainer is a platform for learning system design through Study, Practice, and Mock Interview sessions with explainable evaluation, adaptive recommendation, and later-stage voice interaction.

Its core value is not passive content consumption. The system is meant to help learners **recall, structure, articulate, and defend** solutions in a form close to real system design interviews.

## Start here
- Humans: `docs/00_document_map.md`
- Implementation agents: `AGENTS.md`
- Baseline status: `docs/00_implementation_baseline_v2.2.md`
- Release history: `docs/00_release_notes.md`

## Package highlights
- explicit bounded contexts
- rubric-first hybrid evaluation
- evidence-weighted learner state
- deterministic recommendation policy over a bounded action space
- stable policy surface for future model-assisted ranking
- bundled-but-schema-distinct authoring posture for v1

## Main bounded contexts
1. Content Kernel
2. Learning Design
3. Session Runtime
4. Evaluation Engine
5. Learning Intelligence

## Key decisions already fixed
- only `Study`, `Practice`, and `MockInterview` are top-level runtime modes
- recommendation selects structured learning actions
- learner state uses `proficiency_estimate + confidence`
- learner evidence uses semantic events with coarse timing only
- v1 is text-first; voice is later

## Repository shape
```text
system-design-trainer/
  AGENTS.md
  README.md
  backend/
  docs/
  examples/
  frontend/
  tools/
```

## Current implementation direction

- backend: Python `3.12+` with `FastAPI`
- frontend: separate TypeScript application
- Python tooling and backend share a root `.venv`
- Python verification includes `ruff` plus tests
