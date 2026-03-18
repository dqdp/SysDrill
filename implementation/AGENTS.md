# AGENTS

This file augments the root `AGENTS.md` for the `implementation/` subtree.

If this file conflicts with the root `AGENTS.md`, the root file wins.

## Purpose of this subtree

`implementation/` is the execution layer for the current implementation wave.

It exists to track:
- explicit TDD plans
- bounded implementation slices
- acceptance criteria
- current execution status

It does not replace the knowledge base under `docs/`.

## Local rules

- Do not write or modify product code for a slice unless that slice has an explicit TDD plan.
- Prefer one slice file under `implementation/slices/` per bounded change.
- A valid slice plan must include:
  - goal
  - in-scope and out-of-scope items
  - affected bounded contexts
  - source-of-truth references
  - test contract
  - acceptance criteria
  - definition of done
- After creating or updating a slice plan, review it before coding.
- That review must explicitly look for:
  - weak spots
  - hidden assumptions
  - undefined behavior
  - contradictions inside the plan
  - conflicts with `AGENTS.md`, ADRs, or binding docs under `docs/`
- If any such issue is found, report it to the user together with recommended fixes before writing code.

## Execution hygiene

- Keep `roadmap.md`, `status.md`, and the active slice file in sync.
- When a slice is completed, update its status in the same change set.
- Do not store new architecture decisions here; move those back into the knowledge base.
- Do not let slice docs drift into vague backlog items. Keep them executable.

## Default workflow for a new slice

1. Create or update the slice file.
2. Review the slice for weak spots and conflicts with the knowledge base.
3. Align the reviewed plan with the user.
4. Write red tests first.
5. Implement the minimum change to satisfy the tests.
6. Run verification.
7. Update `status.md` and `roadmap.md` if the slice is completed.
