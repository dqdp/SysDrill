from __future__ import annotations

from typing import Any

_SUBSKILL_TITLES = {
    "tradeoff_reasoning": "Trade-off reasoning",
    "communication_clarity": "Communication clarity",
}


def build_content_title_map(catalog: dict[str, dict[str, Any]]) -> dict[str, str]:
    titles: dict[str, str] = {}
    for bundle in catalog.values():
        topic_package = bundle.get("topic_package", {})
        canonical_content = topic_package.get("canonical_content", {})
        if not isinstance(canonical_content, dict):
            continue
        concepts = canonical_content.get("concepts", [])
        if not isinstance(concepts, list):
            continue
        for concept in concepts:
            if not isinstance(concept, dict):
                continue
            concept_id = _draft_field_value(concept.get("id"))
            concept_title = _draft_field_value(concept.get("title"))
            if isinstance(concept_id, str) and concept_id:
                titles[concept_id] = concept_title if isinstance(concept_title, str) else concept_id
    return titles


def build_learner_summary(
    profile: dict[str, Any],
    content_titles: dict[str, str] | None = None,
) -> dict[str, Any]:
    resolved_titles = {} if content_titles is None else dict(content_titles)
    concept_state = _mapping(profile.get("concept_state"))
    subskill_state = _mapping(profile.get("subskill_state"))
    trajectory_state = _mapping(profile.get("trajectory_state"))
    return {
        "user_id": profile.get("user_id"),
        "weak_areas": _weak_areas(concept_state, subskill_state, resolved_titles),
        "review_due": _review_due(concept_state, resolved_titles),
        "readiness_summary": _readiness_summary(trajectory_state),
        "evidence_posture": _evidence_posture(
            concept_state=concept_state,
            subskill_state=subskill_state,
            trajectory_state=trajectory_state,
        ),
    }


def _weak_areas(
    concept_state: dict[str, Any],
    subskill_state: dict[str, Any],
    content_titles: dict[str, str],
) -> list[dict[str, str]]:
    candidates: list[tuple[float, dict[str, str]]] = []

    for target_id, summary in concept_state.items():
        confidence = _metric(summary, "confidence")
        proficiency = _metric(summary, "proficiency_estimate")
        review_due_risk = _metric(summary, "review_due_risk")
        hint_dependency = _metric(summary, "hint_dependency_signal")
        if confidence < 0.25:
            continue
        if proficiency <= 0.45:
            candidates.append(
                (
                    2.0 - proficiency,
                    {
                        "target_kind": "concept",
                        "target_id": target_id,
                        "title": content_titles.get(target_id, target_id),
                        "posture": "weak",
                        "summary": (
                            "Reviewed evidence still points to a weak concept foundation here."
                        ),
                    },
                )
            )
            continue
        if review_due_risk >= 0.65 and (hint_dependency >= 0.2 or proficiency <= 0.6):
            candidates.append(
                (
                    1.0 + review_due_risk - proficiency,
                    {
                        "target_kind": "concept",
                        "target_id": target_id,
                        "title": content_titles.get(target_id, target_id),
                        "posture": "fragile",
                        "summary": (
                            "Recent success looks fragile enough that this concept still needs attention."
                        ),
                    },
                )
            )

    for subskill_id, summary in subskill_state.items():
        confidence = _metric(summary, "confidence")
        proficiency = _metric(summary, "proficiency_estimate")
        if confidence < 0.25 or proficiency > 0.45:
            continue
        candidates.append(
            (
                1.5 - proficiency,
                {
                    "target_kind": "subskill",
                    "target_id": subskill_id,
                    "title": _SUBSKILL_TITLES.get(subskill_id, subskill_id),
                    "posture": "weak",
                    "summary": "This supported subskill is still weak enough to justify more guided work.",
                },
            )
        )

    candidates.sort(key=lambda entry: (-entry[0], entry[1]["title"]))
    return [payload for _, payload in candidates[:3]]


def _review_due(
    concept_state: dict[str, Any],
    content_titles: dict[str, str],
) -> list[dict[str, str]]:
    candidates: list[tuple[float, dict[str, str]]] = []
    for target_id, summary in concept_state.items():
        confidence = _metric(summary, "confidence")
        review_due_risk = _metric(summary, "review_due_risk")
        if confidence < 0.25 or review_due_risk < 0.55:
            continue
        candidates.append(
            (
                review_due_risk,
                {
                    "target_kind": "concept",
                    "target_id": target_id,
                    "title": content_titles.get(target_id, target_id),
                    "summary": "Recent evidence looks fragile enough that a review pass is due.",
                },
            )
        )
    candidates.sort(key=lambda entry: (-entry[0], entry[1]["title"]))
    return [payload for _, payload in candidates[:3]]


def _readiness_summary(trajectory_state: dict[str, Any]) -> dict[str, str]:
    estimate = _metric(trajectory_state, "mock_readiness_estimate")
    confidence = _metric(trajectory_state, "mock_readiness_confidence")
    fatigue = _metric(trajectory_state, "recent_fatigue_signal")
    abandonment = _metric(trajectory_state, "recent_abandonment_signal")

    if abandonment >= 0.4 or fatigue >= 0.5:
        return {
            "category": "stabilize_first",
            "title": "Stabilize session completion before a mock",
            "detail": "Recent unfinished work is high enough that a lower-pressure step is safer first.",
        }
    if confidence < 0.2:
        return {
            "category": "insufficient_evidence",
            "title": "Mock readiness is still too uncertain",
            "detail": "Need more completed practice evidence before escalating to a readiness check.",
        }
    if estimate >= 0.35 and confidence >= 0.25:
        return {
            "category": "emerging_readiness",
            "title": "Mock readiness is starting to emerge",
            "detail": "The current evidence is improving, but the system should still stay conservative.",
        }
    return {
        "category": "not_ready_yet",
        "title": "A mock would still be premature",
        "detail": "The current learner state still favors more reinforcement or review before escalation.",
    }


def _evidence_posture(
    concept_state: dict[str, Any],
    subskill_state: dict[str, Any],
    trajectory_state: dict[str, Any],
) -> dict[str, Any]:
    if not concept_state and not subskill_state:
        return {
            "category": "insufficient_evidence",
            "title": "There is not enough reviewed evidence yet",
            "details": [
                "Complete a few reviewed sessions before trusting weak-area or readiness summaries."
            ],
        }

    details: list[str] = []
    if any(_metric(summary, "hint_dependency_signal") >= 0.25 for summary in concept_state.values()):
        details.append("Recent work still shows support-dependent evidence.")
    if _metric(trajectory_state, "recent_abandonment_signal") >= 0.25:
        details.append("Recent unfinished sessions lower confidence in the summary.")
    concept_confidences = [_metric(summary, "confidence") for summary in concept_state.values()]
    if len(concept_confidences) < 2 or max(concept_confidences, default=0.0) < 0.5:
        details.append("The current summary is still based on limited repeated evidence.")
    if not details:
        details.append("Recent reviewed evidence is becoming more stable, but the summary remains conservative.")

    return {
        "category": "conservative_summary",
        "title": "The learner summary stays intentionally conservative",
        "details": details,
    }


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _metric(summary: dict[str, Any], field: str) -> float:
    value = summary.get(field, 0.0)
    if not isinstance(value, (int, float)):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _draft_field_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return _draft_field_value(value["value"])
    return value
