# Architecture Agent Guide

Use this guide when changing architecture-related parts of the package or codebase.

## Preserve these boundaries
- Content Kernel != Learning Design
- Learning Intelligence != Session Runtime
- Evaluation Engine != Recommendation Policy

## Read before changing architecture
1. `docs/00_source_of_truth_map.md`
2. `docs/00_agent_invariants.md`
3. `docs/02_domain/bounded_context_map.md`
4. `docs/02_domain/hand_off_contracts.md`
5. relevant ADRs

## Common mistakes to avoid
- turning recommendation into prompt-level orchestration
- treating low confidence as evidence of weakness
- widening event granularity without a decision
- reintroducing `Review` as a top-level mode
- mixing content truth with pedagogical packaging
