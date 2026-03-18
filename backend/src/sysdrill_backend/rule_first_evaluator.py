import hashlib
import json
import re
from typing import Any


class RuleFirstEvaluationError(ValueError):
    pass


_SUPPORTED_BINDING_ID = "binding.concept_recall.v1"
_SUPPORTED_UNIT_FAMILY = "concept_recall"
_RUBRIC_VERSION_REF = "rubric.v1"
_EVALUATOR_VERSION_REF = "rule_first.concept_recall.v1"
_BINDING_VERSION_REF = "binding.concept_recall.v1"

_CRITERION_ORDER = [
    "concept_explanation",
    "usage_judgment",
    "trade_off_articulation",
    "communication_clarity",
]

_CRITERION_METADATA: dict[str, dict[str, Any]] = {
    "concept_explanation": {
        "applicability": "required",
        "weight": 1.3,
        "missing_aspect": "define what the concept is",
    },
    "usage_judgment": {
        "applicability": "required",
        "weight": 1.1,
        "missing_aspect": "explain when to use it",
    },
    "trade_off_articulation": {
        "applicability": "required",
        "weight": 1.0,
        "missing_aspect": "surface the main trade-offs",
    },
    "communication_clarity": {
        "applicability": "secondary",
        "weight": 0.7,
        "missing_aspect": "present the answer in a clearer structure",
    },
}

_EXPLANATION_MARKERS = [
    " is ",
    " are ",
    " means ",
    " refers to ",
    " stores ",
    " storing ",
    " acts as ",
    " lets you ",
    "это ",
    " означает ",
    " хран",
]
_USAGE_MARKERS = [
    " use ",
    " used ",
    " when ",
    " best for ",
    " appropriate ",
    " helps when ",
    " useful for ",
    " suitable for ",
    " read-heavy ",
    " latency-sensitive ",
    " использовать",
    " когда ",
    " подходит",
]
_USAGE_QUALIFIERS = [
    " read-heavy",
    " latency",
    " load",
    " hot path",
    " frequent",
    " repeated",
    " traffic",
    " нагруз",
    " часто",
]
_TRADEOFF_MARKERS = [
    "trade-off",
    "tradeoff",
    "however",
    "but ",
    " downside",
    " drawback",
    " cost",
    " risk",
    " stale",
    " invalidat",
    " memory",
    " complexity",
    " consistency",
    " компромисс",
    " недостат",
    " но ",
]
_TRADEOFF_QUALIFIERS = [
    "stale",
    "invalidation",
    "memory",
    "complexity",
    "consistency",
    "freshness",
    "cost",
    "invalidat",
]


def evaluate_concept_recall(request: dict[str, Any]) -> dict[str, Any]:
    _validate_request(request)
    transcript_text = request["transcript_text"]
    transcript_metrics = _transcript_metrics(transcript_text)
    criterion_results = _build_criterion_results(request, transcript_metrics)
    weighted_score = _weighted_score(criterion_results, request["session_mode"])
    missing_dimensions = [
        criterion["criterion_id"]
        for criterion in criterion_results
        if criterion["criterion_id"] != "communication_clarity" and criterion["score_band"] < 2
    ]
    overall_confidence = _overall_confidence(request, transcript_metrics, missing_dimensions)
    gating_failures = _gating_failures(request, transcript_metrics, missing_dimensions)
    downstream_signals = _downstream_signals(
        request,
        criterion_results,
        weighted_score,
        overall_confidence,
    )
    review_summary = _review_summary(
        criterion_results,
        missing_dimensions,
        downstream_signals,
    )
    evaluation_id = _deterministic_id("evaluation", request)
    evaluation_result = {
        "evaluation_id": evaluation_id,
        "session_id": request["session_id"],
        "unit_id": request["executable_unit_id"],
        "binding_id": request["binding_id"],
        "criterion_results": criterion_results,
        "gating_failures": gating_failures,
        "weighted_score": weighted_score,
        "overall_confidence": overall_confidence,
        "missing_dimensions": missing_dimensions,
        "review_summary": review_summary,
        "summary_feedback": review_summary,
        "downstream_signals": downstream_signals,
        "rubric_version": _RUBRIC_VERSION_REF,
        "rubric_version_ref": _RUBRIC_VERSION_REF,
        "binding_version_ref": _BINDING_VERSION_REF,
        "evaluation_mode": "rule_only",
        "evaluator_version_ref": _EVALUATOR_VERSION_REF,
    }
    review_report = {
        "session_id": request["session_id"],
        "strengths": list(review_summary["strengths"]),
        "missed_dimensions": list(review_summary["missed_dimensions"]),
        "reasoning_gaps": list(review_summary["shallow_areas"]),
        "recommended_next_focus": review_summary["next_focus_suggestion"],
        "linked_evaluation_ids": [evaluation_id],
        "support_dependence_note": review_summary["support_dependence_note"],
    }
    return {
        "evaluation_result": evaluation_result,
        "review_report": review_report,
    }


def _validate_request(request: dict[str, Any]) -> None:
    if request.get("binding_id") != _SUPPORTED_BINDING_ID:
        raise RuleFirstEvaluationError(
            "unsupported binding for rule-first concept recall evaluation: {0}".format(
                request.get("binding_id")
            )
        )
    if request.get("unit_family") != _SUPPORTED_UNIT_FAMILY:
        raise RuleFirstEvaluationError(
            "unsupported unit_family for rule-first concept recall evaluation: {0}".format(
                request.get("unit_family")
            )
        )
    if not isinstance(request.get("transcript_text"), str):
        raise RuleFirstEvaluationError("transcript_text must be a string")
    hint_usage_summary = request.get("hint_usage_summary")
    if not isinstance(hint_usage_summary, dict):
        raise RuleFirstEvaluationError("hint_usage_summary must be a mapping")


def _transcript_metrics(transcript_text: str) -> dict[str, Any]:
    normalized_text = " {0} ".format(re.sub(r"\s+", " ", transcript_text.strip().lower()))
    char_count = len(transcript_text.strip())
    sentence_count = len(
        [part for part in re.split(r"[.!?]+", transcript_text.strip()) if part.strip()]
    )
    return {
        "normalized_text": normalized_text,
        "char_count": char_count,
        "sentence_count": sentence_count,
    }


def _build_criterion_results(
    request: dict[str, Any],
    transcript_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    criterion_results = []
    for criterion_id in _CRITERION_ORDER:
        criterion_results.append(
            _criterion_result(
                request,
                transcript_metrics,
                criterion_id,
            )
        )
    return criterion_results


def _criterion_result(
    request: dict[str, Any],
    transcript_metrics: dict[str, Any],
    criterion_id: str,
) -> dict[str, Any]:
    metadata = _CRITERION_METADATA[criterion_id]
    score_band = _score_band(criterion_id, transcript_metrics)
    observed_evidence = _observed_evidence(criterion_id, transcript_metrics)
    missing_aspects = []
    if score_band < 2:
        missing_aspects.append(metadata["missing_aspect"])
    return {
        "criterion_id": criterion_id,
        "applicability": metadata["applicability"],
        "score_band": score_band,
        "weight": metadata["weight"],
        "weight_used": metadata["weight"],
        "observed_evidence": observed_evidence,
        "missing_aspects": missing_aspects,
        "inferred_judgment": _inferred_judgment(criterion_id, score_band),
        "criterion_confidence": _criterion_confidence(transcript_metrics, score_band),
    }


def _score_band(criterion_id: str, transcript_metrics: dict[str, Any]) -> int:
    normalized_text = transcript_metrics["normalized_text"]
    char_count = transcript_metrics["char_count"]
    sentence_count = transcript_metrics["sentence_count"]
    explanation_marker = _contains_any(normalized_text, _EXPLANATION_MARKERS)
    usage_marker = _contains_any(normalized_text, _USAGE_MARKERS)
    usage_qualifier = _contains_any(normalized_text, _USAGE_QUALIFIERS)
    tradeoff_marker = _contains_any(normalized_text, _TRADEOFF_MARKERS)
    tradeoff_qualifier = _contains_any(normalized_text, _TRADEOFF_QUALIFIERS)

    if criterion_id == "concept_explanation":
        if char_count < 20:
            return 0
        if explanation_marker and char_count >= 110:
            return 3
        if explanation_marker and char_count >= 40:
            return 2
        return 1

    if criterion_id == "usage_judgment":
        if usage_marker and usage_qualifier:
            return 3
        if usage_marker:
            return 2
        if usage_qualifier:
            return 1
        return 0

    if criterion_id == "trade_off_articulation":
        if tradeoff_marker and tradeoff_qualifier:
            return 3
        if tradeoff_marker:
            return 2
        if char_count >= 100 and " but " in normalized_text:
            return 1
        return 0

    if criterion_id == "communication_clarity":
        dimension_hits = sum(
            [
                1 if explanation_marker else 0,
                1 if usage_marker else 0,
                1 if tradeoff_marker else 0,
            ]
        )
        if sentence_count >= 3 and dimension_hits == 3:
            return 3
        if sentence_count >= 2 and char_count >= 80:
            return 2
        if char_count >= 30:
            return 1
        return 0

    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _observed_evidence(criterion_id: str, transcript_metrics: dict[str, Any]) -> list[str]:
    normalized_text = transcript_metrics["normalized_text"]
    char_count = transcript_metrics["char_count"]
    evidence = []

    if criterion_id == "concept_explanation":
        if _contains_any(normalized_text, _EXPLANATION_MARKERS):
            evidence.append("definition-like phrasing is present")
        if char_count >= 40:
            evidence.append("answer contains enough text to attempt a concept explanation")
    elif criterion_id == "usage_judgment":
        if _contains_any(normalized_text, _USAGE_MARKERS):
            evidence.append("usage-oriented cues are present")
        if _contains_any(normalized_text, _USAGE_QUALIFIERS):
            evidence.append("workload or fit cues are present")
    elif criterion_id == "trade_off_articulation":
        if _contains_any(normalized_text, _TRADEOFF_MARKERS):
            evidence.append("trade-off markers are present")
        if _contains_any(normalized_text, _TRADEOFF_QUALIFIERS):
            evidence.append("specific downside cues are present")
    elif criterion_id == "communication_clarity":
        if transcript_metrics["sentence_count"] >= 2:
            evidence.append("answer is structured into multiple sentences")
        if char_count >= 80:
            evidence.append("answer has enough length for a structured explanation")
    return evidence


def _inferred_judgment(criterion_id: str, score_band: int) -> str:
    if criterion_id == "concept_explanation":
        if score_band >= 3:
            return "The learner explains the concept clearly and with working depth."
        if score_band == 2:
            return "The learner gives a usable explanation, but it remains compact."
        if score_band == 1:
            return "The learner hints at the concept, but the explanation is shallow."
        return "The learner does not yet provide a usable concept explanation."

    if criterion_id == "usage_judgment":
        if score_band >= 3:
            return "The learner explains when the concept fits and ties it to workload shape."
        if score_band == 2:
            return "The learner mentions when to use the concept, but without much nuance."
        if score_band == 1:
            return "The learner hints at motivation, but not at clear usage boundaries."
        return "The learner does not explain when the concept should be used."

    if criterion_id == "trade_off_articulation":
        if score_band >= 3:
            return "The learner surfaces concrete trade-offs and implementation costs."
        if score_band == 2:
            return "The learner mentions trade-offs, but the downsides stay high level."
        if score_band == 1:
            return "The learner gestures at downsides without making them concrete."
        return "The learner does not surface the main trade-offs."

    if criterion_id == "communication_clarity":
        if score_band >= 3:
            return "The answer is easy to follow and interview-readable."
        if score_band == 2:
            return "The answer is mostly clear, but the structure could be sharper."
        if score_band == 1:
            return "The answer is readable, but under-structured."
        return "The answer is too thin to judge communication clarity well."

    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _criterion_confidence(transcript_metrics: dict[str, Any], score_band: int) -> float:
    char_count = transcript_metrics["char_count"]
    if char_count < 20:
        base_confidence = 0.2
    elif char_count < 50:
        base_confidence = 0.45
    elif char_count < 100:
        base_confidence = 0.65
    else:
        base_confidence = 0.8
    if score_band == 0:
        base_confidence -= 0.05
    return round(max(0.1, min(1.0, base_confidence)), 2)


def _weighted_score(
    criterion_results: list[dict[str, Any]],
    session_mode: str,
) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for criterion in criterion_results:
        normalized_score = criterion["score_band"] / 3.0
        weighted_sum += normalized_score * criterion["weight_used"]
        total_weight += criterion["weight_used"]
    if total_weight == 0:
        return 0.0
    weighted_score = weighted_sum / total_weight
    if session_mode == "Practice":
        weighted_score *= 0.9
    return round(weighted_score, 4)


def _overall_confidence(
    request: dict[str, Any],
    transcript_metrics: dict[str, Any],
    missing_dimensions: list[str],
) -> float:
    char_count = transcript_metrics["char_count"]
    if char_count < 20:
        confidence = 0.2
    elif char_count < 50:
        confidence = 0.45
    elif char_count < 100:
        confidence = 0.65
    else:
        confidence = 0.8
    if missing_dimensions:
        confidence -= min(0.2, 0.05 * len(missing_dimensions))

    hint_usage_summary = request["hint_usage_summary"]
    if hint_usage_summary.get("hint_count", 0) > 0 or hint_usage_summary.get(
        "used_prior_hints", False
    ):
        confidence -= 0.1
    if request.get("answer_reveal_flag", False):
        confidence -= 0.15
    return round(max(0.1, min(1.0, confidence)), 2)


def _gating_failures(
    request: dict[str, Any],
    transcript_metrics: dict[str, Any],
    missing_dimensions: list[str],
) -> list[str]:
    if request.get("completion_status") != "submitted":
        return ["evaluation_request is not in submitted state"]
    if transcript_metrics["char_count"] == 0:
        return ["no substantive learner answer was captured"]
    if len(missing_dimensions) == 3:
        return ["answer misses all primary concept-recall dimensions"]
    return []


def _downstream_signals(
    request: dict[str, Any],
    criterion_results: list[dict[str, Any]],
    weighted_score: float,
    overall_confidence: float,
) -> dict[str, Any]:
    score_by_criterion = {
        criterion["criterion_id"]: criterion["score_band"] for criterion in criterion_results
    }
    hint_usage_summary = request["hint_usage_summary"]
    hint_dependency = 0.0
    if hint_usage_summary.get("hint_count", 0) > 0:
        hint_dependency += 0.35
    if hint_usage_summary.get("used_prior_hints", False):
        hint_dependency += 0.2
    if request.get("answer_reveal_flag", False):
        hint_dependency += 0.35

    return {
        "coverage_gap": round(
            max(0.0, (3 - score_by_criterion["concept_explanation"]) / 3.0),
            4,
        ),
        "usage_gap": round(
            max(0.0, (3 - score_by_criterion["usage_judgment"]) / 3.0),
            4,
        ),
        "tradeoff_gap": round(
            max(0.0, (3 - score_by_criterion["trade_off_articulation"]) / 3.0),
            4,
        ),
        "communication_gap": round(
            max(0.0, (3 - score_by_criterion["communication_clarity"]) / 3.0),
            4,
        ),
        "hint_dependency": round(min(1.0, hint_dependency), 4),
        "strong_independent_performance": bool(
            weighted_score >= 0.75 and overall_confidence >= 0.7 and hint_dependency == 0.0
        ),
    }


def _review_summary(
    criterion_results: list[dict[str, Any]],
    missing_dimensions: list[str],
    downstream_signals: dict[str, Any],
) -> dict[str, Any]:
    strengths = []
    shallow_areas = []
    for criterion in criterion_results:
        if criterion["score_band"] >= 2:
            strengths.append(_strength_line(criterion["criterion_id"]))
        elif criterion["score_band"] == 1:
            shallow_areas.append(_shallow_line(criterion["criterion_id"]))

    missed_dimensions = [_dimension_label(dimension) for dimension in missing_dimensions]
    if missed_dimensions:
        next_focus_suggestion = (
            "Next, give the answer in three parts: what it is, when to use it, "
            "and the main trade-offs."
        )
    else:
        next_focus_suggestion = (
            "Next, keep the same structure and add one concrete example or boundary case."
        )

    support_dependence_note = None
    if downstream_signals["hint_dependency"] > 0.0:
        support_dependence_note = (
            "Support usage lowers confidence in fully independent recall for this attempt."
        )

    return {
        "strengths": strengths,
        "missed_dimensions": missed_dimensions,
        "shallow_areas": shallow_areas,
        "next_focus_suggestion": next_focus_suggestion,
        "support_dependence_note": support_dependence_note,
    }


def _strength_line(criterion_id: str) -> str:
    if criterion_id == "concept_explanation":
        return "The answer explains the concept itself in working terms."
    if criterion_id == "usage_judgment":
        return "The answer names when the concept fits the workload."
    if criterion_id == "trade_off_articulation":
        return "The answer surfaces concrete trade-offs instead of only benefits."
    if criterion_id == "communication_clarity":
        return "The answer is structured and easy to follow."
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _shallow_line(criterion_id: str) -> str:
    if criterion_id == "concept_explanation":
        return "The concept explanation is still too thin to stand on its own."
    if criterion_id == "usage_judgment":
        return "The answer hints at usage, but does not set clear fit boundaries."
    if criterion_id == "trade_off_articulation":
        return "The answer gestures at trade-offs without making the downsides concrete."
    if criterion_id == "communication_clarity":
        return "The answer is readable, but the structure could be sharper."
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _dimension_label(criterion_id: str) -> str:
    if criterion_id == "concept_explanation":
        return "what the concept is"
    if criterion_id == "usage_judgment":
        return "when to use it"
    if criterion_id == "trade_off_articulation":
        return "the main trade-offs"
    if criterion_id == "communication_clarity":
        return "clear answer structure"
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _contains_any(text: str, candidates: list[str]) -> bool:
    return any(candidate in text for candidate in candidates)


def _deterministic_id(prefix: str, request: dict[str, Any]) -> str:
    stable_payload = json.dumps(request, sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(stable_payload.encode("utf-8")).hexdigest()[:12]
    return "{0}.{1}".format(prefix, digest)
