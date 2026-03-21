from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


class LearnerProjector:
    def build_profile(self, runtime_reader: Any, user_id: str) -> dict[str, Any]:
        # Rebuild-on-read keeps projection deterministic while history is still process-local.
        sessions = runtime_reader.list_user_sessions(user_id)
        concept_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
        subskill_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
        latest_activity_at: str | None = None
        reviewed_session_count = 0
        practice_or_mock_review_count = 0

        for session in sessions:
            session_events = runtime_reader.list_session_events(session["session_id"])
            session_latest_at = _latest_timestamp(
                [event.get("occurred_at") for event in session_events]
            )
            latest_activity_at = _later_timestamp(latest_activity_at, session_latest_at)

            evaluation_result = session.get("last_evaluation_result")
            if not isinstance(evaluation_result, dict):
                continue

            reviewed_session_count += 1
            if session.get("mode") in {"Practice", "MockInterview"}:
                practice_or_mock_review_count += 1

            content_id = _session_content_id(session)
            if content_id is not None and session_latest_at is not None:
                concept_evidence[content_id].append(
                    _concept_evidence_point(
                        session=session,
                        evaluation_result=evaluation_result,
                        evidence_at=session_latest_at,
                    )
                )

            for subskill_id, evidence_point in _subskill_evidence_points(
                session=session,
                evaluation_result=evaluation_result,
                evidence_at=session_latest_at,
            ).items():
                subskill_evidence[subskill_id].append(evidence_point)

        concept_state = _build_concept_state(concept_evidence, latest_activity_at)
        subskill_state = _build_subskill_state(subskill_evidence)
        trajectory_state = _build_trajectory_state(
            concept_state=concept_state,
            subskill_state=subskill_state,
            reviewed_session_count=reviewed_session_count,
            practice_or_mock_review_count=practice_or_mock_review_count,
            last_active_at=latest_activity_at,
        )

        return {
            "user_id": user_id,
            "concept_state": concept_state,
            "subskill_state": subskill_state,
            "trajectory_state": trajectory_state,
            "last_updated_at": latest_activity_at,
        }


def _build_concept_state(
    concept_evidence: dict[str, list[dict[str, Any]]],
    latest_activity_at: str | None,
) -> dict[str, dict[str, Any]]:
    concept_state: dict[str, dict[str, Any]] = {}
    for content_id in sorted(concept_evidence):
        evidence_points = concept_evidence[content_id]
        total_weight = sum(point["weight"] for point in evidence_points)
        proficiency_estimate = _weighted_average(evidence_points, "proficiency_signal")
        hint_dependency_signal = _weighted_average(evidence_points, "hint_dependency")
        overall_confidence = _weighted_average(evidence_points, "overall_confidence")
        count_factor = min(1.0, len(evidence_points) / 3.0)
        confidence = _clamp(
            0.05
            + 0.35 * overall_confidence * (1.0 - hint_dependency_signal)
            + 0.25 * count_factor
        )
        recency_factor = _recency_factor(
            latest_activity_at=latest_activity_at,
            evidence_at=_latest_timestamp(point["evidence_at"] for point in evidence_points),
        )
        review_due_risk = _clamp(
            0.45 * (1.0 - proficiency_estimate)
            + 0.25 * hint_dependency_signal
            + 0.2 * recency_factor
            + 0.1 * (1.0 - confidence)
        )
        last_evidence_at = _latest_timestamp(point["evidence_at"] for point in evidence_points)

        concept_state[content_id] = {
            "proficiency_estimate": _round_metric(proficiency_estimate),
            "confidence": _round_metric(confidence),
            "review_due_risk": _round_metric(review_due_risk),
            "hint_dependency_signal": _round_metric(hint_dependency_signal),
            "last_evidence_at": last_evidence_at,
        }

        if total_weight <= 0.0:
            concept_state[content_id]["proficiency_estimate"] = 0.0
            concept_state[content_id]["confidence"] = 0.0

    return concept_state


def _build_subskill_state(
    subskill_evidence: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    subskill_state: dict[str, dict[str, Any]] = {}
    for subskill_id in sorted(subskill_evidence):
        evidence_points = subskill_evidence[subskill_id]
        proficiency_estimate = _weighted_average(evidence_points, "proficiency_signal")
        hint_dependency_signal = _weighted_average(evidence_points, "hint_dependency")
        criterion_confidence = _weighted_average(evidence_points, "criterion_confidence")
        count_factor = min(1.0, len(evidence_points) / 3.0)
        confidence = _clamp(
            0.05
            + 0.35 * criterion_confidence * (1.0 - hint_dependency_signal)
            + 0.25 * count_factor
        )

        subskill_state[subskill_id] = {
            "proficiency_estimate": _round_metric(proficiency_estimate),
            "confidence": _round_metric(confidence),
            "last_evidence_at": _latest_timestamp(
                point["evidence_at"] for point in evidence_points
            ),
        }

    return subskill_state


def _build_trajectory_state(
    concept_state: dict[str, dict[str, Any]],
    subskill_state: dict[str, dict[str, Any]],
    reviewed_session_count: int,
    practice_or_mock_review_count: int,
    last_active_at: str | None,
) -> dict[str, Any]:
    if not concept_state:
        return {
            "recent_fatigue_signal": 0.0,
            "recent_abandonment_signal": 0.0,
            "mock_readiness_estimate": 0.0,
            "mock_readiness_confidence": 0.0,
            "last_active_at": last_active_at,
        }

    average_concept_proficiency = _average_from_state(concept_state, "proficiency_estimate")
    average_concept_confidence = _average_from_state(concept_state, "confidence")
    average_supported_subskills = _average_from_state(subskill_state, "proficiency_estimate")
    practice_factor = 0.0
    if reviewed_session_count > 0:
        practice_factor = min(1.0, practice_or_mock_review_count / reviewed_session_count)

    mock_readiness_estimate = _clamp(
        min(
            0.45,
            0.2 * average_concept_proficiency
            + 0.15 * average_supported_subskills
            + 0.1 * practice_factor,
        )
    )
    mock_readiness_confidence = _clamp(
        min(
            0.35,
            0.05
            + 0.15 * practice_factor
            + 0.15 * min(1.0, reviewed_session_count / 3.0) * average_concept_confidence,
        )
    )

    return {
        # These remain explicit zero baselines until runtime emits the needed events.
        "recent_fatigue_signal": 0.0,
        "recent_abandonment_signal": 0.0,
        "mock_readiness_estimate": _round_metric(mock_readiness_estimate),
        "mock_readiness_confidence": _round_metric(mock_readiness_confidence),
        "last_active_at": last_active_at,
    }


def _concept_evidence_point(
    session: dict[str, Any],
    evaluation_result: dict[str, Any],
    evidence_at: str,
) -> dict[str, Any]:
    criterion_results = _criterion_results_by_id(evaluation_result)
    concept_explanation = _normalized_score(criterion_results.get("concept_explanation"))
    usage_judgment = _normalized_score(criterion_results.get("usage_judgment"))
    support_hint_dependency = _hint_dependency(evaluation_result)
    concept_score = (
        (1.3 * concept_explanation + 1.1 * usage_judgment)
        / (1.3 + 1.1)
    )
    mode = session.get("mode")
    mode_weight = 1.0 if mode == "Study" else 0.97 if mode == "Practice" else 0.94

    return {
        "weight": 1.0,
        "proficiency_signal": _clamp(
            concept_score * mode_weight * (1.0 - 0.25 * support_hint_dependency)
        ),
        "overall_confidence": _clamp(float(evaluation_result.get("overall_confidence", 0.0))),
        "hint_dependency": support_hint_dependency,
        "evidence_at": evidence_at,
    }


def _subskill_evidence_points(
    session: dict[str, Any],
    evaluation_result: dict[str, Any],
    evidence_at: str | None,
) -> dict[str, dict[str, Any]]:
    if evidence_at is None:
        return {}

    criterion_results = _criterion_results_by_id(evaluation_result)
    hint_dependency = _hint_dependency(evaluation_result)
    mode = session.get("mode")
    mode_weight = 0.78 if mode == "Study" else 1.0 if mode == "Practice" else 1.05

    mapping = {
        "tradeoff_reasoning": criterion_results.get("trade_off_articulation"),
        "communication_clarity": criterion_results.get("communication_clarity"),
    }
    evidence_points: dict[str, dict[str, Any]] = {}
    for subskill_id, criterion_result in mapping.items():
        if not isinstance(criterion_result, dict):
            continue
        evidence_points[subskill_id] = {
            "weight": 1.0,
            "proficiency_signal": _clamp(
                _normalized_score(criterion_result)
                * mode_weight
                * (1.0 - 0.2 * hint_dependency)
            ),
            "criterion_confidence": _clamp(
                float(criterion_result.get("criterion_confidence", 0.0))
            ),
            "hint_dependency": hint_dependency,
            "evidence_at": evidence_at,
        }

    return evidence_points


def _criterion_results_by_id(evaluation_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    criterion_results = evaluation_result.get("criterion_results", [])
    if not isinstance(criterion_results, list):
        return {}

    indexed: dict[str, dict[str, Any]] = {}
    for criterion_result in criterion_results:
        if not isinstance(criterion_result, dict):
            continue
        criterion_id = criterion_result.get("criterion_id")
        if isinstance(criterion_id, str) and criterion_id:
            indexed[criterion_id] = criterion_result
    return indexed


def _normalized_score(criterion_result: dict[str, Any] | None) -> float:
    if not isinstance(criterion_result, dict):
        return 0.0
    score_band = criterion_result.get("score_band", 0)
    if not isinstance(score_band, (int, float)):
        return 0.0
    return _clamp(float(score_band) / 3.0)


def _hint_dependency(evaluation_result: dict[str, Any]) -> float:
    downstream_signals = evaluation_result.get("downstream_signals", {})
    if not isinstance(downstream_signals, dict):
        return 0.0
    value = downstream_signals.get("hint_dependency", 0.0)
    if not isinstance(value, (int, float)):
        return 0.0
    return _clamp(float(value))


def _weighted_average(evidence_points: list[dict[str, Any]], field: str) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for point in evidence_points:
        weight = point.get("weight", 0.0)
        value = point.get(field, 0.0)
        if not isinstance(weight, (int, float)) or not isinstance(value, (int, float)):
            continue
        weighted_sum += float(weight) * float(value)
        total_weight += float(weight)

    if total_weight == 0.0:
        return 0.0
    return _clamp(weighted_sum / total_weight)


def _average_from_state(state: dict[str, dict[str, Any]], field: str) -> float:
    if not state:
        return 0.0
    values = [
        float(payload[field])
        for payload in state.values()
        if isinstance(payload.get(field), (int, float))
    ]
    if not values:
        return 0.0
    return _clamp(sum(values) / len(values))


def _session_content_id(session: dict[str, Any]) -> str | None:
    current_unit = session.get("current_unit")
    if not isinstance(current_unit, dict):
        return None
    source_content_ids = current_unit.get("source_content_ids", [])
    if not isinstance(source_content_ids, list) or not source_content_ids:
        return None
    content_id = source_content_ids[0]
    if not isinstance(content_id, str) or not content_id:
        return None
    return content_id


def _latest_timestamp(values: Any) -> str | None:
    latest_value: str | None = None
    latest_at: datetime | None = None
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        parsed = _parse_timestamp(value)
        if parsed is None:
            continue
        if latest_at is None or parsed > latest_at:
            latest_at = parsed
            latest_value = value
    return latest_value


def _later_timestamp(left: str | None, right: str | None) -> str | None:
    return _latest_timestamp([left, right])


def _parse_timestamp(value: str) -> datetime | None:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _recency_factor(latest_activity_at: str | None, evidence_at: str | None) -> float:
    if latest_activity_at is None or evidence_at is None:
        return 0.0
    latest_activity = _parse_timestamp(latest_activity_at)
    evidence_time = _parse_timestamp(evidence_at)
    if latest_activity is None or evidence_time is None or latest_activity <= evidence_time:
        return 0.0
    age_seconds = (latest_activity - evidence_time).total_seconds()
    return _clamp(age_seconds / (7 * 24 * 60 * 60))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _round_metric(value: float) -> float:
    return round(_clamp(value), 4)
