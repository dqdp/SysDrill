# Implementation Layer

This directory is the execution layer for the current implementation wave.

It is intentionally separate from the knowledge base under `docs/`.

## Purpose

Use this directory to track:
- execution order
- bounded TDD slices
- acceptance criteria
- current status and blockers

## Non-goals

Do not use this directory as:
- a second source of truth for architecture
- a replacement for ADRs
- a replacement for domain or contract docs
- a backlog of speculative ideas

## Authority boundary

If any file here conflicts with:
- `AGENTS.md`
- `docs/00_source_of_truth_map.md`
- binding contract docs under `docs/`
- ADRs under `docs/adr/`

then the knowledge base wins.

## Update rules

- Keep slice docs execution-oriented.
- Record only the minimum context needed to implement the next bounded change.
- Put architecture or contract changes back into the knowledge base, not here.
- When a slice is finished, update `status.md` and the slice file in the same change set.
- Prefer one slice per commit when feasible.

## Layout

- `roadmap.md`: ordered implementation slices
- `status.md`: current state, active slice, blockers
- `slices/*.md`: per-slice TDD contracts and definition of done
