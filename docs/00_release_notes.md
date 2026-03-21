# Release Notes

## Unreleased
- added initial `FastAPI` backend scaffold under `backend/`
- added root Python tooling posture with `Makefile`-based verification hooks
- added root `ruff` configuration for Python code
- documented current implementation direction as Python backend plus separate TypeScript frontend
- added a deterministic rule-first review loop for the bounded `concept_recall`
  runtime path
- added `docs/03_architecture/concept_recall_binding_v1.md` and aligned
  evaluation docs with the prototype binding
- hardened the manual runtime/content path against duplicate in-process session
  transitions, symlinked configured export roots, nullable bundle summary
  sections, and malformed draft-loading env during health-only bootstrap
- added the first scenario-backed `URL Shortener` draft fixture plus a bounded
  `MockInterview / ReadinessCheck` executable unit family as the `013a`
  unblocker, while keeping recommendation/runtime behavior scoped away from
  `013b`

## v2.2 — implementation baseline designation
- marked v2.2 as the implementation baseline for the first controlled implementation wave
- added `docs/00_implementation_baseline_v2.2.md`
- updated agent-facing documents to distinguish:
  - frozen baseline decisions
  - implementation-ready source-of-truth contracts
  - orientation-only documents
  - watch areas during implementation
- updated change protocol to preserve the implementation baseline by default and require explicit revision discipline for baseline changes

## v2.1 — architecture/evaluation hardening
- strengthened `target_architecture_v1.md` into a more implementation-ready architecture contract
- strengthened `evaluation_engine_v1.md` into a clearer request/result/pipeline contract
- clarified the boundary between `metrics_and_assurance.md` and `evaluation_quality_plan_v1.md`
- added `implementation_mapping_v1.md` for implementation-agent module/code mapping

## v2.0
- hardened package for use as an implementation-agent knowledge base
- added `AGENTS.md`
- added `00_source_of_truth_map.md`, `00_agent_invariants.md`, `00_change_protocol.md`
- added `session_runtime_state_machine_v1.md`
- added `evaluation_quality_plan_v1.md`
- cleaned `domain_model.md` and `hand_off_contracts.md`
- reduced overload in `README.md` and `00_document_map.md`

## v1.9
- recommendation ranking now distinguishes completion/momentum policy envelope from instructional ranking priority
- ranking priority fixed as: confirmed remediation, then spaced review due, then progression/readiness escalation

## v1.8
- split recommendation docs into policy, surface, and decision logging/offline evaluation
- added ADR-010 for deterministic v1 policy surface with future model extension

## v1.7
- replaced `mastery` with `proficiency_estimate + confidence`
- added `learner_state_update_rules_v1.md`

## v1.6
- fixed authoring posture as bundled-but-schema-distinct with progressive coverage
- added `authoring_model_v1.md`

## v1.5
- fixed event granularity to semantic learning events with coarse timing only

## v1.4
- recommendation now selects structured learning actions rather than raw content items

## v1.3
- strengthened product-facing framing, card taxonomy, and MVP content bootstrap

## v1.2
- fixed modes model to `Study`, `Practice`, `MockInterview` plus `Session Intent`

## v1.1
- strengthened Content Kernel / Learning Design boundary and executable rubric contract
