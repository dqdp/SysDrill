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
_URL_SHORTENER_BINDING_ID = "binding.url_shortener.v1"
_URL_SHORTENER_UNIT_FAMILY = "scenario_readiness_check"
_URL_SHORTENER_EVALUATOR_VERSION_REF = "rule_first.url_shortener.v1"
_URL_SHORTENER_BINDING_VERSION_REF = "binding.url_shortener.v1"
_RATE_LIMITER_BINDING_ID = "binding.rate_limiter.v1"
_RATE_LIMITER_UNIT_FAMILY = "scenario_readiness_check"
_RATE_LIMITER_EVALUATOR_VERSION_REF = "rule_first.rate_limiter.v1"
_RATE_LIMITER_BINDING_VERSION_REF = "binding.rate_limiter.v1"

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
_URL_SHORTENER_CRITERION_ORDER = [
    "requirements_understanding",
    "decomposition_quality",
    "data_and_storage_choices",
    "scaling_strategy",
    "reliability_awareness",
    "trade_off_articulation",
    "communication_clarity",
]
_URL_SHORTENER_CRITERION_METADATA: dict[str, dict[str, Any]] = {
    "requirements_understanding": {
        "applicability": "required",
        "weight": 1.0,
        "missing_aspect": "state the read-heavy and availability requirements",
    },
    "decomposition_quality": {
        "applicability": "required",
        "weight": 1.2,
        "missing_aspect": "decompose the system into redirect, id, and storage paths",
    },
    "data_and_storage_choices": {
        "applicability": "required",
        "weight": 1.2,
        "missing_aspect": "name a concrete mapping store and access pattern",
    },
    "scaling_strategy": {
        "applicability": "required",
        "weight": 1.2,
        "missing_aspect": "explain how the read-heavy path scales",
    },
    "reliability_awareness": {
        "applicability": "secondary",
        "weight": 0.7,
        "missing_aspect": "surface availability or correctness risks",
    },
    "trade_off_articulation": {
        "applicability": "required",
        "weight": 1.0,
        "missing_aspect": "defend the main trade-offs",
    },
    "communication_clarity": {
        "applicability": "secondary",
        "weight": 0.7,
        "missing_aspect": "present the design in a clearer sequence",
    },
}
_URL_SHORTENER_REQUIREMENT_MARKERS = [
    "read-heavy",
    "availability",
    "high availability",
    "latency",
    "redirect",
]
_URL_SHORTENER_COMPONENT_MARKERS = [
    "redirect",
    "api",
    "service",
    "store",
    "storage",
    "database",
    "cache",
    "counter",
    "id generation",
]
_URL_SHORTENER_STORAGE_MARKERS = [
    "store",
    "storage",
    "database",
    "db",
    "mapping",
    "key-value",
    "kv",
]
_URL_SHORTENER_SCALING_MARKERS = [
    "cache",
    "read-heavy",
    "replica",
    "replication",
    "shard",
    "scal",
    "throughput",
]
_URL_SHORTENER_RELIABILITY_MARKERS = [
    "availability",
    "collision",
    "retry",
    "replica",
    "replication",
    "failover",
    "durable",
    "correctness",
]
_URL_SHORTENER_ID_MARKERS = [
    "id",
    "identifier",
    "counter",
    "random",
    "base62",
    "slug",
    "collision",
]
_URL_SHORTENER_ALLOWED_CONCEPT_IDS = {
    "concept.url-shortener.id-generation",
    "concept.url-shortener.storage-choice",
    "concept.url-shortener.read-scaling",
    "concept.url-shortener.caching",
}
_RATE_LIMITER_CRITERION_ORDER = [
    "requirements_understanding",
    "decomposition_quality",
    "data_and_storage_choices",
    "reliability_awareness",
    "trade_off_articulation",
    "scaling_strategy",
    "communication_clarity",
]
_RATE_LIMITER_CRITERION_METADATA: dict[str, dict[str, Any]] = {
    "requirements_understanding": {
        "applicability": "required",
        "weight": 1.1,
        "missing_aspect": "state the multi-tenant fairness requirement",
    },
    "decomposition_quality": {
        "applicability": "required",
        "weight": 1.0,
        "missing_aspect": "separate the limiter, counter, and enforcement path",
    },
    "data_and_storage_choices": {
        "applicability": "required",
        "weight": 1.2,
        "missing_aspect": "name the counter placement and rate-limiting semantics",
    },
    "reliability_awareness": {
        "applicability": "required",
        "weight": 1.2,
        "missing_aspect": "explain behavior when shared state is stale or unavailable",
    },
    "trade_off_articulation": {
        "applicability": "required",
        "weight": 1.0,
        "missing_aspect": "defend correctness versus latency trade-offs",
    },
    "scaling_strategy": {
        "applicability": "secondary",
        "weight": 0.8,
        "missing_aspect": "describe cross-node scaling implications",
    },
    "communication_clarity": {
        "applicability": "secondary",
        "weight": 0.7,
        "missing_aspect": "present the design in a clearer sequence",
    },
}
_RATE_LIMITER_REQUIREMENT_MARKERS = [
    "tenant",
    "multi-tenant",
    "api",
    "fair",
    "fairness",
    "request",
]
_RATE_LIMITER_COMPONENT_MARKERS = [
    "limiter",
    "counter",
    "bucket",
    "window",
    "redis",
    "state",
]
_RATE_LIMITER_ALGORITHM_MARKERS = [
    "token bucket",
    "leaky bucket",
    "fixed window",
    "sliding window",
    "bucket",
    "window",
]
_RATE_LIMITER_STATE_MARKERS = [
    "redis",
    "counter",
    "shared state",
    "state store",
    "distributed",
    "centralized",
    "centralised",
    "region",
    "regions",
]
_RATE_LIMITER_SCALING_MARKERS = [
    "distributed",
    "region",
    "regions",
    "node",
    "nodes",
    "instance",
    "instances",
    "throughput",
    "scale",
]
_RATE_LIMITER_FAILURE_CONTEXT_MARKERS = [
    "unavailable",
    "stale",
    "lagging",
    "fallback",
    "degraded",
    "fail-open",
    "fail open",
    "fail-closed",
    "fail closed",
]
_RATE_LIMITER_FAILURE_ACTION_MARKERS = [
    "fail-open",
    "fail open",
    "fail-closed",
    "fail closed",
    "fallback",
    "degraded",
    "reject",
    "allow",
    "block",
    "bypass",
    "error response",
]
_RATE_LIMITER_FAILURE_UNCERTAINTY_MARKERS = [
    "not decided",
    "have not decided",
    "not sure",
    "have not explained",
    "did not explain",
]
_RATE_LIMITER_TRADEOFF_DOMAIN_MARKERS = [
    "fairness",
    "latency",
    "burst",
    "throughput",
    "strict",
    "consistency",
    "availability",
]
_RATE_LIMITER_ALLOWED_CONCEPT_IDS = {
    "concept.rate-limiter.algorithm-choice",
    "concept.rate-limiter.state-placement",
    "concept.rate-limiter.failure-handling",
    "concept.rate-limiter.trade-offs",
}


def evaluate_request(request: dict[str, Any]) -> dict[str, Any]:
    binding_id = request.get("binding_id")
    if binding_id == _SUPPORTED_BINDING_ID:
        return evaluate_concept_recall(request)
    if binding_id == _URL_SHORTENER_BINDING_ID:
        return evaluate_url_shortener_readiness(request)
    if binding_id == _RATE_LIMITER_BINDING_ID:
        return evaluate_rate_limiter_readiness(request)
    raise RuleFirstEvaluationError(
        "unsupported binding for rule-first evaluation: {0}".format(binding_id)
    )


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


def evaluate_url_shortener_readiness(request: dict[str, Any]) -> dict[str, Any]:
    _validate_url_shortener_request(request)
    primary_metrics = _transcript_metrics(request["transcript_text"])
    follow_up_metrics = _transcript_metrics(request["follow_up_transcript_text"])
    combined_metrics = _combine_transcript_metrics(primary_metrics, follow_up_metrics)
    criterion_results = _build_url_shortener_criterion_results(
        primary_metrics=primary_metrics,
        follow_up_metrics=follow_up_metrics,
        combined_metrics=combined_metrics,
    )
    missing_dimensions = [
        criterion["criterion_id"]
        for criterion in criterion_results
        if criterion["applicability"] == "required" and criterion["score_band"] < 2
    ]
    overall_confidence = _scenario_overall_confidence(
        request,
        combined_metrics,
        missing_dimensions,
    )
    gating_failures = _url_shortener_gating_failures(request, combined_metrics)
    weighted_score = _scenario_weighted_score(criterion_results, request["session_mode"])
    downstream_signals = _url_shortener_downstream_signals(
        request=request,
        criterion_results=criterion_results,
        follow_up_metrics=follow_up_metrics,
        combined_metrics=combined_metrics,
        weighted_score=weighted_score,
        overall_confidence=overall_confidence,
        gating_failures=gating_failures,
    )
    review_summary = _url_shortener_review_summary(
        criterion_results=criterion_results,
        missing_dimensions=missing_dimensions,
        downstream_signals=downstream_signals,
        follow_up_metrics=follow_up_metrics,
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
        "binding_version_ref": _URL_SHORTENER_BINDING_VERSION_REF,
        "evaluation_mode": "rule_only",
        "evaluator_version_ref": _URL_SHORTENER_EVALUATOR_VERSION_REF,
    }
    review_report = {
        "session_id": request["session_id"],
        "strengths": list(review_summary["strengths"]),
        "missed_dimensions": list(review_summary["missed_dimensions"]),
        "reasoning_gaps": list(review_summary["shallow_areas"]),
        "recommended_next_focus": review_summary["next_focus_suggestion"],
        "linked_evaluation_ids": [evaluation_id],
        "support_dependence_note": review_summary["support_dependence_note"],
        "follow_up_handling_note": review_summary["follow_up_handling_note"],
    }
    return {
        "evaluation_result": evaluation_result,
        "review_report": review_report,
    }


def evaluate_rate_limiter_readiness(request: dict[str, Any]) -> dict[str, Any]:
    _validate_rate_limiter_request(request)
    primary_metrics = _transcript_metrics(request["transcript_text"])
    follow_up_metrics = _transcript_metrics(request["follow_up_transcript_text"])
    combined_metrics = _combine_transcript_metrics(primary_metrics, follow_up_metrics)
    criterion_results = _build_rate_limiter_criterion_results(
        primary_metrics=primary_metrics,
        follow_up_metrics=follow_up_metrics,
        combined_metrics=combined_metrics,
    )
    missing_dimensions = [
        criterion["criterion_id"]
        for criterion in criterion_results
        if criterion["applicability"] == "required" and criterion["score_band"] < 2
    ]
    overall_confidence = _scenario_overall_confidence(
        request,
        combined_metrics,
        missing_dimensions,
    )
    gating_failures = _rate_limiter_gating_failures(request, combined_metrics)
    weighted_score = _scenario_weighted_score(criterion_results, request["session_mode"])
    downstream_signals = _rate_limiter_downstream_signals(
        request=request,
        criterion_results=criterion_results,
        combined_metrics=combined_metrics,
        weighted_score=weighted_score,
        overall_confidence=overall_confidence,
        gating_failures=gating_failures,
    )
    review_summary = _rate_limiter_review_summary(
        criterion_results=criterion_results,
        missing_dimensions=missing_dimensions,
        downstream_signals=downstream_signals,
        combined_metrics=combined_metrics,
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
        "binding_version_ref": _RATE_LIMITER_BINDING_VERSION_REF,
        "evaluation_mode": "rule_only",
        "evaluator_version_ref": _RATE_LIMITER_EVALUATOR_VERSION_REF,
    }
    review_report = {
        "session_id": request["session_id"],
        "strengths": list(review_summary["strengths"]),
        "missed_dimensions": list(review_summary["missed_dimensions"]),
        "reasoning_gaps": list(review_summary["shallow_areas"]),
        "recommended_next_focus": review_summary["next_focus_suggestion"],
        "linked_evaluation_ids": [evaluation_id],
        "support_dependence_note": review_summary["support_dependence_note"],
        "follow_up_handling_note": review_summary["follow_up_handling_note"],
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


def _validate_url_shortener_request(request: dict[str, Any]) -> None:
    if request.get("binding_id") != _URL_SHORTENER_BINDING_ID:
        raise RuleFirstEvaluationError(
            "unsupported binding for rule-first url-shortener evaluation: {0}".format(
                request.get("binding_id")
            )
        )
    if request.get("unit_family") != _URL_SHORTENER_UNIT_FAMILY:
        raise RuleFirstEvaluationError(
            "unsupported unit_family for url-shortener evaluation: {0}".format(
                request.get("unit_family")
            )
        )
    if request.get("scenario_family") != "url_shortener":
        raise RuleFirstEvaluationError(
            "unsupported scenario_family for url-shortener evaluation: {0}".format(
                request.get("scenario_family")
            )
        )
    if not isinstance(request.get("transcript_text"), str):
        raise RuleFirstEvaluationError("transcript_text must be a string")
    if not isinstance(request.get("follow_up_transcript_text"), str):
        raise RuleFirstEvaluationError("follow_up_transcript_text must be a string")
    hint_usage_summary = request.get("hint_usage_summary")
    if not isinstance(hint_usage_summary, dict):
        raise RuleFirstEvaluationError("hint_usage_summary must be a mapping")


def _validate_rate_limiter_request(request: dict[str, Any]) -> None:
    if request.get("binding_id") != _RATE_LIMITER_BINDING_ID:
        raise RuleFirstEvaluationError(
            "unsupported binding for rule-first rate-limiter evaluation: {0}".format(
                request.get("binding_id")
            )
        )
    if request.get("unit_family") != _RATE_LIMITER_UNIT_FAMILY:
        raise RuleFirstEvaluationError(
            "unsupported unit_family for rate-limiter evaluation: {0}".format(
                request.get("unit_family")
            )
        )
    if request.get("scenario_family") != "rate_limiter":
        raise RuleFirstEvaluationError(
            "unsupported scenario_family for rate-limiter evaluation: {0}".format(
                request.get("scenario_family")
            )
        )
    if not isinstance(request.get("transcript_text"), str):
        raise RuleFirstEvaluationError("transcript_text must be a string")
    if not isinstance(request.get("follow_up_transcript_text"), str):
        raise RuleFirstEvaluationError("follow_up_transcript_text must be a string")
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


def _combine_transcript_metrics(
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
) -> dict[str, Any]:
    combined_text = " ".join(
        [
            primary_metrics["normalized_text"].strip(),
            follow_up_metrics["normalized_text"].strip(),
        ]
    ).strip()
    return {
        "normalized_text": " {0} ".format(combined_text) if combined_text else "  ",
        "char_count": primary_metrics["char_count"] + follow_up_metrics["char_count"],
        "sentence_count": primary_metrics["sentence_count"] + follow_up_metrics["sentence_count"],
    }


def _build_url_shortener_criterion_results(
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    criterion_results = []
    for criterion_id in _URL_SHORTENER_CRITERION_ORDER:
        metadata = _URL_SHORTENER_CRITERION_METADATA[criterion_id]
        score_band = _url_shortener_score_band(
            criterion_id=criterion_id,
            primary_metrics=primary_metrics,
            follow_up_metrics=follow_up_metrics,
            combined_metrics=combined_metrics,
        )
        missing_aspects = []
        if metadata["applicability"] == "required" and score_band < 2:
            missing_aspects.append(metadata["missing_aspect"])
        criterion_results.append(
            {
                "criterion_id": criterion_id,
                "applicability": metadata["applicability"],
                "score_band": score_band,
                "weight": metadata["weight"],
                "weight_used": metadata["weight"],
                "observed_evidence": _url_shortener_observed_evidence(
                    criterion_id,
                    primary_metrics,
                    follow_up_metrics,
                    combined_metrics,
                ),
                "missing_aspects": missing_aspects,
                "criterion_confidence": _criterion_confidence(combined_metrics, score_band),
            }
        )
    return criterion_results


def _url_shortener_score_band(
    criterion_id: str,
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> int:
    combined_text = combined_metrics["normalized_text"]
    follow_up_text = follow_up_metrics["normalized_text"]
    if criterion_id == "requirements_understanding":
        requirement_cues = (
            int("read-heavy" in combined_text)
            + int(_contains_any(combined_text, ["availability", "high availability"]))
            + int(_contains_any(combined_text, ["latency", "redirect"]))
        )
        return _score_from_count(requirement_cues)
    if criterion_id == "decomposition_quality":
        return _score_from_count(_marker_hits(combined_text, _URL_SHORTENER_COMPONENT_MARKERS))
    if criterion_id == "data_and_storage_choices":
        storage_cues = int(_contains_any(combined_text, _URL_SHORTENER_STORAGE_MARKERS))
        mapping_cues = int(
            _contains_any(
                combined_text,
                ["mapping", "long url", "short url", "lookup", "redirect"],
            )
        )
        id_cues = int(_contains_any(follow_up_text, _URL_SHORTENER_ID_MARKERS))
        return _score_from_count(storage_cues + mapping_cues + id_cues)
    if criterion_id == "scaling_strategy":
        scaling_cues = (
            int(_contains_any(combined_text, ["cache", "caching"]))
            + int(_contains_any(combined_text, ["read-heavy", "redirect"]))
            + int(_contains_any(combined_text, ["replica", "replication", "shard", "scale"]))
        )
        return _score_from_count(scaling_cues)
    if criterion_id == "reliability_awareness":
        return _score_from_count(_marker_hits(combined_text, _URL_SHORTENER_RELIABILITY_MARKERS))
    if criterion_id == "trade_off_articulation":
        tradeoff_score = int(_contains_any(combined_text, _TRADEOFF_MARKERS)) + int(
            _contains_any(combined_text, _TRADEOFF_QUALIFIERS)
        )
        return _score_from_count(tradeoff_score)
    if criterion_id == "communication_clarity":
        if combined_metrics["char_count"] >= 180 and combined_metrics["sentence_count"] >= 3:
            return 3
        if combined_metrics["char_count"] >= 90 and combined_metrics["sentence_count"] >= 2:
            return 2
        if combined_metrics["char_count"] >= 40:
            return 1
        return 0
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _url_shortener_observed_evidence(
    criterion_id: str,
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> list[str]:
    combined_text = combined_metrics["normalized_text"]
    follow_up_text = follow_up_metrics["normalized_text"]
    if criterion_id == "requirements_understanding":
        return _evidence_lines(
            [
                ("Mentions the read-heavy workload.", "read-heavy" in combined_text),
                (
                    "Surfaces availability pressure.",
                    _contains_any(combined_text, ["availability", "high availability"]),
                ),
                ("Keeps the redirect path in scope.", "redirect" in combined_text),
            ]
        )
    if criterion_id == "decomposition_quality":
        return _evidence_lines(
            [
                ("Names the redirect/read path.", "redirect" in combined_text),
                ("Calls out storage or a database layer.", "storage" in combined_text),
                (
                    "Separates identifier generation.",
                    _contains_any(
                        combined_text,
                        ["counter", "random", "id generation", "collision"],
                    ),
                ),
            ]
        )
    if criterion_id == "data_and_storage_choices":
        return _evidence_lines(
            [
                (
                    "Names a concrete mapping store.",
                    _contains_any(combined_text, _URL_SHORTENER_STORAGE_MARKERS),
                ),
                ("Frames the short-id to URL mapping.", "mapping" in combined_text),
                (
                    "Defends the identifier strategy in the follow-up.",
                    _contains_any(follow_up_text, _URL_SHORTENER_ID_MARKERS),
                ),
            ]
        )
    if criterion_id == "scaling_strategy":
        return _evidence_lines(
            [
                ("Uses caching on the redirect path.", "cache" in combined_text),
                ("Recognizes the read-heavy traffic shape.", "read-heavy" in combined_text),
                (
                    "Mentions replica, shard, or scale-out handling.",
                    _contains_any(combined_text, ["replica", "shard", "scale"]),
                ),
            ]
        )
    if criterion_id == "reliability_awareness":
        return _evidence_lines(
            [
                (
                    "Names availability or durability concerns.",
                    _contains_any(
                        combined_text,
                        ["availability", "durable", "replica", "failover"],
                    ),
                ),
                (
                    "Calls out collision or correctness risk.",
                    _contains_any(combined_text, ["collision", "correctness"]),
                ),
            ]
        )
    if criterion_id == "trade_off_articulation":
        return _evidence_lines(
            [
                (
                    "Notes at least one design trade-off.",
                    _contains_any(combined_text, _TRADEOFF_MARKERS),
                ),
                (
                    "Makes the downside concrete.",
                    _contains_any(combined_text, _TRADEOFF_QUALIFIERS),
                ),
            ]
        )
    if criterion_id == "communication_clarity":
        return _evidence_lines(
            [
                (
                    "Uses multiple sentences to structure the answer.",
                    combined_metrics["sentence_count"] >= 2,
                ),
                (
                    "Provides enough detail for a bounded review.",
                    combined_metrics["char_count"] >= 90,
                ),
            ]
        )
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _scenario_overall_confidence(
    request: dict[str, Any],
    combined_metrics: dict[str, Any],
    missing_dimensions: list[str],
) -> float:
    char_count = combined_metrics["char_count"]
    if char_count < 80:
        confidence = 0.45
    elif char_count < 140:
        confidence = 0.62
    elif char_count < 220:
        confidence = 0.76
    else:
        confidence = 0.84
    if missing_dimensions:
        confidence -= min(0.2, 0.04 * len(missing_dimensions))
    hint_usage_summary = request["hint_usage_summary"]
    if hint_usage_summary.get("hint_count", 0) > 0 or hint_usage_summary.get(
        "used_prior_hints", False
    ):
        confidence -= 0.1
    if request.get("answer_reveal_flag", False):
        confidence -= 0.15
    if not request.get("follow_up_transcript_text", "").strip():
        confidence -= 0.15
    return round(max(0.1, min(1.0, confidence)), 2)


def _url_shortener_gating_failures(
    request: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> list[str]:
    if request.get("completion_status") != "submitted":
        return ["evaluation_request is not in submitted state"]
    if combined_metrics["char_count"] == 0:
        return ["no substantive learner answer was captured"]
    combined_text = combined_metrics["normalized_text"]
    missing_id_anchor = not _contains_any(combined_text, _URL_SHORTENER_ID_MARKERS)
    missing_scaling_anchor = not _contains_any(
        combined_text,
        ["cache", "read-heavy", "replica", "shard", "scale"],
    )
    missing_storage_anchor = not _contains_any(
        combined_text,
        ["store", "storage", "database", "mapping", "key-value", "lookup"],
    )
    if missing_id_anchor and missing_scaling_anchor and missing_storage_anchor:
        return ["answer misses the required url-shortener design anchors"]
    return []


def _scenario_weighted_score(
    criterion_results: list[dict[str, Any]],
    session_mode: str,
) -> float:
    weighted_sum = 0.0
    weight_total = 0.0
    for criterion in criterion_results:
        weight = criterion["weight_used"]
        weighted_sum += (criterion["score_band"] / 3.0) * weight
        weight_total += weight
    if weight_total == 0:
        return 0.0
    weighted_score = weighted_sum / weight_total
    if session_mode == "Study":
        weighted_score = min(1.0, weighted_score + 0.02)
    return round(weighted_score, 4)


def _url_shortener_downstream_signals(
    request: dict[str, Any],
    criterion_results: list[dict[str, Any]],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
    weighted_score: float,
    overall_confidence: float,
    gating_failures: list[str],
) -> dict[str, Any]:
    criterion_results_by_id = {
        criterion["criterion_id"]: criterion for criterion in criterion_results
    }
    score_by_criterion = {
        criterion_id: criterion["score_band"]
        for criterion_id, criterion in criterion_results_by_id.items()
    }
    hint_usage_summary = request["hint_usage_summary"]
    hint_dependency = 0.0
    if hint_usage_summary.get("hint_count", 0) > 0:
        hint_dependency += 0.35
    if hint_usage_summary.get("used_prior_hints", False):
        hint_dependency += 0.2
    if request.get("answer_reveal_flag", False):
        hint_dependency += 0.35
    concept_mock_evidence = _url_shortener_concept_mock_evidence(
        request=request,
        criterion_results_by_id=criterion_results_by_id,
        follow_up_metrics=follow_up_metrics,
        combined_metrics=combined_metrics,
        overall_confidence=overall_confidence,
        gating_failures=gating_failures,
    )
    return {
        "requirements_gap": round(
            max(0.0, (3 - score_by_criterion["requirements_understanding"]) / 3.0),
            4,
        ),
        "decomposition_gap": round(
            max(0.0, (3 - score_by_criterion["decomposition_quality"]) / 3.0),
            4,
        ),
        "storage_gap": round(
            max(0.0, (3 - score_by_criterion["data_and_storage_choices"]) / 3.0),
            4,
        ),
        "scaling_gap": round(
            max(0.0, (3 - score_by_criterion["scaling_strategy"]) / 3.0),
            4,
        ),
        "tradeoff_gap": round(
            max(0.0, (3 - score_by_criterion["trade_off_articulation"]) / 3.0),
            4,
        ),
        "hint_dependency": round(min(1.0, hint_dependency), 4),
        "concept_mock_evidence": concept_mock_evidence,
        "bounded_mock_pass": bool(
            weighted_score >= 0.65
            and overall_confidence >= 0.65
            and not gating_failures
            and score_by_criterion["trade_off_articulation"] >= 2
            and score_by_criterion["communication_clarity"] >= 2
        ),
    }


def _url_shortener_review_summary(
    criterion_results: list[dict[str, Any]],
    missing_dimensions: list[str],
    downstream_signals: dict[str, Any],
    follow_up_metrics: dict[str, Any],
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
            "Next, structure the answer around requirements, core components, "
            "read-path scaling, and one defended trade-off."
        )
    else:
        next_focus_suggestion = (
            "Next, keep the same structure and add one explicit failure mode or "
            "abuse-control boundary."
        )

    support_dependence_note = None
    if downstream_signals["hint_dependency"] > 0.0:
        support_dependence_note = (
            "Support usage lowers confidence in fully independent mock readiness."
        )

    follow_up_handling_note = "Follow-up handling still needs a more concrete identifier strategy."
    if _contains_any(
        follow_up_metrics["normalized_text"],
        ["counter", "random", "collision", "base62"],
    ):
        follow_up_handling_note = (
            "Follow-up handling stayed concrete enough to defend the identifier strategy."
        )

    return {
        "strengths": strengths,
        "missed_dimensions": missed_dimensions,
        "shallow_areas": shallow_areas,
        "next_focus_suggestion": next_focus_suggestion,
        "support_dependence_note": support_dependence_note,
        "follow_up_handling_note": follow_up_handling_note,
    }


def _build_rate_limiter_criterion_results(
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    criterion_results = []
    for criterion_id in _RATE_LIMITER_CRITERION_ORDER:
        metadata = _RATE_LIMITER_CRITERION_METADATA[criterion_id]
        score_band = _rate_limiter_score_band(
            criterion_id=criterion_id,
            primary_metrics=primary_metrics,
            follow_up_metrics=follow_up_metrics,
            combined_metrics=combined_metrics,
        )
        missing_aspects = []
        if metadata["applicability"] == "required" and score_band < 2:
            missing_aspects.append(metadata["missing_aspect"])
        criterion_results.append(
            {
                "criterion_id": criterion_id,
                "applicability": metadata["applicability"],
                "score_band": score_band,
                "weight": metadata["weight"],
                "weight_used": metadata["weight"],
                "observed_evidence": _rate_limiter_observed_evidence(
                    criterion_id,
                    primary_metrics,
                    follow_up_metrics,
                    combined_metrics,
                ),
                "missing_aspects": missing_aspects,
                "criterion_confidence": _criterion_confidence(combined_metrics, score_band),
            }
        )
    return criterion_results


def _rate_limiter_score_band(
    criterion_id: str,
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> int:
    combined_text = combined_metrics["normalized_text"]
    follow_up_text = follow_up_metrics["normalized_text"]
    if criterion_id == "requirements_understanding":
        requirement_cues = _marker_hits(combined_text, _RATE_LIMITER_REQUIREMENT_MARKERS)
        return _score_from_count(requirement_cues)
    if criterion_id == "decomposition_quality":
        return _score_from_count(_marker_hits(combined_text, _RATE_LIMITER_COMPONENT_MARKERS))
    if criterion_id == "data_and_storage_choices":
        storage_cues = int(_contains_any(combined_text, _RATE_LIMITER_STATE_MARKERS))
        algorithm_cues = int(_contains_any(combined_text, _RATE_LIMITER_ALGORITHM_MARKERS))
        return _score_from_count(storage_cues + algorithm_cues)
    if criterion_id == "reliability_awareness":
        reliability_cues = int(_rate_limiter_has_explicit_failure_policy(follow_up_text)) + int(
            _contains_any(combined_text, ["stale", "lagging", "unavailable", "fallback"])
        )
        return _score_from_count(reliability_cues)
    if criterion_id == "trade_off_articulation":
        tradeoff_score = int(_contains_any(combined_text, _TRADEOFF_MARKERS)) + int(
            _contains_any(combined_text, _RATE_LIMITER_TRADEOFF_DOMAIN_MARKERS)
        )
        return _score_from_count(tradeoff_score)
    if criterion_id == "scaling_strategy":
        return _score_from_count(_marker_hits(combined_text, _RATE_LIMITER_SCALING_MARKERS))
    if criterion_id == "communication_clarity":
        if combined_metrics["char_count"] >= 180 and combined_metrics["sentence_count"] >= 3:
            return 3
        if combined_metrics["char_count"] >= 90 and combined_metrics["sentence_count"] >= 2:
            return 2
        if combined_metrics["char_count"] >= 40:
            return 1
        return 0
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _rate_limiter_observed_evidence(
    criterion_id: str,
    primary_metrics: dict[str, Any],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> list[str]:
    combined_text = combined_metrics["normalized_text"]
    follow_up_text = follow_up_metrics["normalized_text"]
    if criterion_id == "requirements_understanding":
        return _evidence_lines(
            [
                (
                    "Mentions tenant or fairness requirements.",
                    _contains_any(combined_text, ["tenant", "fair", "fairness"]),
                ),
                (
                    "Keeps request limits in scope.",
                    _contains_any(combined_text, ["request", "rate limiter", "limiter"]),
                ),
            ]
        )
    if criterion_id == "decomposition_quality":
        return _evidence_lines(
            [
                ("Names the limiter itself.", "limiter" in combined_text),
                (
                    "Calls out counters or shared state.",
                    _contains_any(combined_text, ["counter", "state", "redis"]),
                ),
                (
                    "Mentions an enforcement algorithm.",
                    _contains_any(combined_text, _RATE_LIMITER_ALGORITHM_MARKERS),
                ),
            ]
        )
    if criterion_id == "data_and_storage_choices":
        return _evidence_lines(
            [
                (
                    "Names a concrete state placement.",
                    _contains_any(combined_text, _RATE_LIMITER_STATE_MARKERS),
                ),
                (
                    "Names an explicit rate-limiting algorithm.",
                    _contains_any(combined_text, _RATE_LIMITER_ALGORITHM_MARKERS),
                ),
            ]
        )
    if criterion_id == "reliability_awareness":
        return _evidence_lines(
            [
                (
                    "Mentions stale or unavailable state handling.",
                    _contains_any(combined_text, ["stale", "lagging", "unavailable"]),
                ),
                (
                    "Provides a concrete degraded policy in the follow-up.",
                    _rate_limiter_has_explicit_failure_policy(follow_up_text),
                ),
            ]
        )
    if criterion_id == "trade_off_articulation":
        return _evidence_lines(
            [
                (
                    "Names a domain trade-off.",
                    _contains_any(combined_text, _TRADEOFF_MARKERS),
                ),
                (
                    "Makes the fairness, latency, or burst trade-off concrete.",
                    _contains_any(combined_text, _RATE_LIMITER_TRADEOFF_DOMAIN_MARKERS),
                ),
            ]
        )
    if criterion_id == "scaling_strategy":
        return _evidence_lines(
            [
                (
                    "Mentions cross-node or regional deployment pressure.",
                    _contains_any(combined_text, _RATE_LIMITER_SCALING_MARKERS),
                ),
            ]
        )
    if criterion_id == "communication_clarity":
        return _evidence_lines(
            [
                (
                    "Uses multiple sentences to structure the answer.",
                    combined_metrics["sentence_count"] >= 2,
                ),
                (
                    "Provides enough detail for a bounded review.",
                    combined_metrics["char_count"] >= 90,
                ),
            ]
        )
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _rate_limiter_gating_failures(
    request: dict[str, Any],
    combined_metrics: dict[str, Any],
) -> list[str]:
    if request.get("completion_status") != "submitted":
        return ["evaluation_request is not in submitted state"]
    if combined_metrics["char_count"] == 0:
        return ["no substantive learner answer was captured"]
    combined_text = combined_metrics["normalized_text"]
    missing_state_anchor = not _contains_any(combined_text, _RATE_LIMITER_STATE_MARKERS)
    missing_algorithm_anchor = not _contains_any(combined_text, _RATE_LIMITER_ALGORITHM_MARKERS)
    missing_failure_anchor = not _rate_limiter_has_explicit_failure_policy(combined_text)
    if missing_state_anchor and missing_algorithm_anchor and missing_failure_anchor:
        return ["answer misses the required rate-limiter design anchors"]
    return []


def _rate_limiter_downstream_signals(
    request: dict[str, Any],
    criterion_results: list[dict[str, Any]],
    combined_metrics: dict[str, Any],
    weighted_score: float,
    overall_confidence: float,
    gating_failures: list[str],
) -> dict[str, Any]:
    criterion_results_by_id = {
        criterion["criterion_id"]: criterion for criterion in criterion_results
    }
    score_by_criterion = {
        criterion_id: criterion["score_band"]
        for criterion_id, criterion in criterion_results_by_id.items()
    }
    hint_usage_summary = request["hint_usage_summary"]
    hint_dependency = 0.0
    if hint_usage_summary.get("hint_count", 0) > 0:
        hint_dependency += 0.35
    if hint_usage_summary.get("used_prior_hints", False):
        hint_dependency += 0.2
    if request.get("answer_reveal_flag", False):
        hint_dependency += 0.35
    concept_mock_evidence = _rate_limiter_concept_mock_evidence(
        request=request,
        criterion_results_by_id=criterion_results_by_id,
        combined_metrics=combined_metrics,
        overall_confidence=overall_confidence,
        gating_failures=gating_failures,
    )
    return {
        "requirements_gap": round(
            max(0.0, (3 - score_by_criterion["requirements_understanding"]) / 3.0),
            4,
        ),
        "decomposition_gap": round(
            max(0.0, (3 - score_by_criterion["decomposition_quality"]) / 3.0),
            4,
        ),
        "storage_gap": round(
            max(0.0, (3 - score_by_criterion["data_and_storage_choices"]) / 3.0),
            4,
        ),
        "scaling_gap": round(
            max(0.0, (3 - score_by_criterion["scaling_strategy"]) / 3.0),
            4,
        ),
        "tradeoff_gap": round(
            max(0.0, (3 - score_by_criterion["trade_off_articulation"]) / 3.0),
            4,
        ),
        "hint_dependency": round(min(1.0, hint_dependency), 4),
        "concept_mock_evidence": concept_mock_evidence,
        "bounded_mock_pass": bool(
            weighted_score >= 0.65
            and overall_confidence >= 0.65
            and not gating_failures
            and score_by_criterion["trade_off_articulation"] >= 2
            and score_by_criterion["communication_clarity"] >= 2
        ),
    }


def _rate_limiter_review_summary(
    criterion_results: list[dict[str, Any]],
    missing_dimensions: list[str],
    downstream_signals: dict[str, Any],
    combined_metrics: dict[str, Any],
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
            "Next, structure the answer around limiter semantics, state placement, "
            "degraded behavior, and one defended fairness trade-off."
        )
    else:
        next_focus_suggestion = (
            "Next, keep the same structure and add one more explicit degraded-mode boundary."
        )

    support_dependence_note = None
    if downstream_signals["hint_dependency"] > 0.0:
        support_dependence_note = (
            "Support usage lowers confidence in fully independent mock readiness."
        )

    follow_up_handling_note = (
        "Follow-up handling still needs a concrete degraded policy when limiter state is stale "
        "or unavailable."
    )
    if _rate_limiter_has_explicit_failure_policy(combined_metrics["normalized_text"]):
        follow_up_handling_note = (
            "Follow-up handling stayed concrete enough to defend degraded behavior."
        )

    return {
        "strengths": strengths,
        "missed_dimensions": missed_dimensions,
        "shallow_areas": shallow_areas,
        "next_focus_suggestion": next_focus_suggestion,
        "support_dependence_note": support_dependence_note,
        "follow_up_handling_note": follow_up_handling_note,
    }


def _rate_limiter_concept_mock_evidence(
    request: dict[str, Any],
    criterion_results_by_id: dict[str, dict[str, Any]],
    combined_metrics: dict[str, Any],
    overall_confidence: float,
    gating_failures: list[str],
) -> list[dict[str, Any]]:
    allowed_concept_ids = _allowed_mock_concept_ids(request, _RATE_LIMITER_ALLOWED_CONCEPT_IDS)
    concept_signals: list[dict[str, Any]] = []
    combined_text = combined_metrics["normalized_text"]

    if combined_metrics["char_count"] < 110 or combined_metrics["sentence_count"] < 2:
        return concept_signals

    missing_algorithm_choice = not _contains_any(combined_text, _RATE_LIMITER_ALGORITHM_MARKERS)
    missing_state_placement = not _contains_any(combined_text, _RATE_LIMITER_STATE_MARKERS)
    missing_failure_handling = not _rate_limiter_has_explicit_failure_policy(combined_text)

    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.rate-limiter.algorithm-choice",
        signal_strength=0.72,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["data_and_storage_choices"],
            overall_confidence,
        ),
        source_criteria=["data_and_storage_choices"],
        evidence_basis=["expected_cue_missing"],
        condition=missing_algorithm_choice,
    )
    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.rate-limiter.state-placement",
        signal_strength=0.7 if not gating_failures else 0.82,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["data_and_storage_choices"],
            overall_confidence,
        ),
        source_criteria=["data_and_storage_choices"],
        evidence_basis=["explicit_gap"] if not gating_failures else ["gating_failure"],
        condition=missing_state_placement,
    )
    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.rate-limiter.failure-handling",
        signal_strength=0.8 if not gating_failures else 0.86,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["reliability_awareness"],
            overall_confidence,
        ),
        source_criteria=["reliability_awareness"],
        evidence_basis=["expected_cue_missing"] if not gating_failures else ["gating_failure"],
        condition=missing_failure_handling,
    )
    return concept_signals


def _rate_limiter_has_explicit_failure_policy(text: str) -> bool:
    has_context = _contains_any(text, _RATE_LIMITER_FAILURE_CONTEXT_MARKERS)
    if not has_context:
        return False
    if _contains_any(text, _RATE_LIMITER_FAILURE_UNCERTAINTY_MARKERS):
        return False
    return _contains_any(text, _RATE_LIMITER_FAILURE_ACTION_MARKERS)


def _url_shortener_concept_mock_evidence(
    request: dict[str, Any],
    criterion_results_by_id: dict[str, dict[str, Any]],
    follow_up_metrics: dict[str, Any],
    combined_metrics: dict[str, Any],
    overall_confidence: float,
    gating_failures: list[str],
) -> list[dict[str, Any]]:
    allowed_concept_ids = _allowed_mock_concept_ids(request, _URL_SHORTENER_ALLOWED_CONCEPT_IDS)
    concept_signals: list[dict[str, Any]] = []
    combined_text = combined_metrics["normalized_text"]
    follow_up_text = follow_up_metrics["normalized_text"]

    missing_identifier_strategy = not _contains_any(follow_up_text, _URL_SHORTENER_ID_MARKERS)
    missing_storage_choice = not _contains_any(combined_text, _URL_SHORTENER_STORAGE_MARKERS)
    missing_scaling_anchor = not _contains_any(
        combined_text,
        ["replica", "replication", "shard", "scale", "throughput"],
    )
    cache_expected = _contains_any(combined_text, ["read-heavy", "redirect"])
    missing_cache = cache_expected and not _contains_any(combined_text, ["cache", "caching"])

    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.url-shortener.id-generation",
        signal_strength=0.72,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["data_and_storage_choices"],
            overall_confidence,
        ),
        source_criteria=["data_and_storage_choices"],
        evidence_basis=["expected_cue_missing"],
        condition=missing_identifier_strategy,
    )
    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.url-shortener.storage-choice",
        signal_strength=0.82 if gating_failures else 0.7,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["data_and_storage_choices"],
            overall_confidence,
        ),
        source_criteria=["data_and_storage_choices"],
        evidence_basis=["gating_failure"] if gating_failures else ["explicit_gap"],
        condition=missing_storage_choice,
    )
    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.url-shortener.read-scaling",
        signal_strength=0.74 if gating_failures else 0.66,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["scaling_strategy"],
            overall_confidence,
        ),
        source_criteria=["scaling_strategy"],
        evidence_basis=["gating_failure"] if gating_failures else ["expected_cue_missing"],
        condition=missing_scaling_anchor,
    )
    _append_negative_mock_concept_signal(
        concept_signals=concept_signals,
        allowed_concept_ids=allowed_concept_ids,
        concept_id="concept.url-shortener.caching",
        signal_strength=0.56,
        signal_confidence=_concept_signal_confidence(
            criterion_results_by_id,
            ["scaling_strategy"],
            overall_confidence,
        ),
        source_criteria=["scaling_strategy"],
        evidence_basis=["expected_cue_missing"],
        condition=missing_cache,
    )
    return concept_signals


def _allowed_mock_concept_ids(
    request: dict[str, Any],
    allowed_concept_pool: set[str],
) -> set[str]:
    bound_concept_ids = request.get("bound_concept_ids")
    if not isinstance(bound_concept_ids, list) or not bound_concept_ids:
        return set(allowed_concept_pool)
    allowed = {
        concept_id
        for concept_id in bound_concept_ids
        if isinstance(concept_id, str) and concept_id in allowed_concept_pool
    }
    return allowed if allowed else set(allowed_concept_pool)


def _concept_signal_confidence(
    criterion_results_by_id: dict[str, dict[str, Any]],
    source_criteria: list[str],
    overall_confidence: float,
) -> float:
    criterion_confidences = [
        float(criterion_results_by_id[criterion_id].get("criterion_confidence", overall_confidence))
        for criterion_id in source_criteria
        if isinstance(criterion_results_by_id.get(criterion_id), dict)
    ]
    if criterion_confidences:
        average_confidence = sum(criterion_confidences) / len(criterion_confidences)
        return round(
            max(
                0.1,
                min(1.0, min(overall_confidence, average_confidence)),
            ),
            2,
        )
    return round(max(0.1, min(1.0, overall_confidence)), 2)


def _append_negative_mock_concept_signal(
    concept_signals: list[dict[str, Any]],
    allowed_concept_ids: set[str],
    concept_id: str,
    signal_strength: float,
    signal_confidence: float,
    source_criteria: list[str],
    evidence_basis: list[str],
    condition: bool,
) -> None:
    if not condition or concept_id not in allowed_concept_ids:
        return
    concept_signals.append(
        {
            "signal_type": "concept_mock_evidence",
            "concept_id": concept_id,
            "direction": "negative",
            "signal_strength": round(max(0.0, min(1.0, signal_strength)), 2),
            "signal_confidence": round(max(0.0, min(1.0, signal_confidence)), 2),
            "source_criteria": list(source_criteria),
            "evidence_basis": list(evidence_basis),
        }
    )


def _strength_line(criterion_id: str) -> str:
    if criterion_id == "concept_explanation":
        return "The answer explains the concept itself in working terms."
    if criterion_id == "usage_judgment":
        return "The answer names when the concept fits the workload."
    if criterion_id == "trade_off_articulation":
        return "The answer surfaces concrete trade-offs instead of only benefits."
    if criterion_id == "communication_clarity":
        return "The answer is structured and easy to follow."
    if criterion_id == "requirements_understanding":
        return "The answer keeps the read-heavy and availability requirements in scope."
    if criterion_id == "decomposition_quality":
        return "The answer decomposes the system into concrete responsibilities."
    if criterion_id == "data_and_storage_choices":
        return "The answer names a plausible mapping store and access path."
    if criterion_id == "scaling_strategy":
        return "The answer explains how the redirect path scales under read-heavy load."
    if criterion_id == "reliability_awareness":
        return "The answer surfaces correctness or availability risks worth defending."
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
    if criterion_id == "requirements_understanding":
        return "The workload requirements are implied, but not stated clearly enough."
    if criterion_id == "decomposition_quality":
        return "The design mentions pieces, but not in a stable system shape."
    if criterion_id == "data_and_storage_choices":
        return "Storage and mapping choices are still too generic."
    if criterion_id == "scaling_strategy":
        return "The answer hints at scaling, but the read path is not defended clearly."
    if criterion_id == "reliability_awareness":
        return "Reliability and correctness risks are still shallow."
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
    if criterion_id == "requirements_understanding":
        return "requirements understanding"
    if criterion_id == "decomposition_quality":
        return "system decomposition"
    if criterion_id == "data_and_storage_choices":
        return "data and storage choices"
    if criterion_id == "scaling_strategy":
        return "scaling strategy"
    if criterion_id == "reliability_awareness":
        return "reliability awareness"
    raise RuleFirstEvaluationError("unsupported criterion_id: {0}".format(criterion_id))


def _contains_any(text: str, candidates: list[str]) -> bool:
    return any(candidate in text for candidate in candidates)


def _marker_hits(text: str, candidates: list[str]) -> int:
    return sum(1 for candidate in candidates if candidate in text)


def _score_from_count(count: int) -> int:
    if count >= 3:
        return 3
    if count == 2:
        return 2
    if count == 1:
        return 1
    return 0


def _evidence_lines(candidates: list[tuple[str, bool]]) -> list[str]:
    return [line for line, matched in candidates if matched]


def _deterministic_id(prefix: str, request: dict[str, Any]) -> str:
    stable_payload = json.dumps(request, sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(stable_payload.encode("utf-8")).hexdigest()[:12]
    return "{0}.{1}".format(prefix, digest)
