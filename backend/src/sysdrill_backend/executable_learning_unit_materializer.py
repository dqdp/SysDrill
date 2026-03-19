from typing import Any


class ExecutableLearningUnitMaterializationError(ValueError):
    pass


_SUPPORTED_UNIT_POLICIES: dict[tuple[str, str], dict[str, Any]] = {
    ("Study", "LearnNew"): {
        "effective_difficulty": "introductory",
        "allowed_hint_levels": [1, 2, 3],
        "follow_up_envelope": {
            "max_follow_ups": 0,
            "follow_up_style": "none",
        },
        "completion_rules": {
            "submission_kind": "manual_submit",
            "answer_boundary": "single_response",
            "allows_answer_reveal": True,
        },
    },
    ("Study", "Reinforce"): {
        "effective_difficulty": "standard",
        "allowed_hint_levels": [1, 2, 3],
        "follow_up_envelope": {
            "max_follow_ups": 0,
            "follow_up_style": "none",
        },
        "completion_rules": {
            "submission_kind": "manual_submit",
            "answer_boundary": "single_response",
            "allows_answer_reveal": True,
        },
    },
    ("Study", "SpacedReview"): {
        "effective_difficulty": "standard",
        "allowed_hint_levels": [1, 2, 3],
        "follow_up_envelope": {
            "max_follow_ups": 0,
            "follow_up_style": "none",
        },
        "completion_rules": {
            "submission_kind": "manual_submit",
            "answer_boundary": "single_response",
            "allows_answer_reveal": True,
        },
    },
    ("Practice", "Reinforce"): {
        "effective_difficulty": "standard",
        "allowed_hint_levels": [1, 2],
        "follow_up_envelope": {
            "max_follow_ups": 1,
            "follow_up_style": "bounded_probe",
        },
        "completion_rules": {
            "submission_kind": "manual_submit",
            "answer_boundary": "single_response",
            "allows_answer_reveal": False,
        },
    },
    ("Practice", "Remediate"): {
        "effective_difficulty": "targeted",
        "allowed_hint_levels": [1, 2],
        "follow_up_envelope": {
            "max_follow_ups": 1,
            "follow_up_style": "bounded_probe",
        },
        "completion_rules": {
            "submission_kind": "manual_submit",
            "answer_boundary": "single_response",
            "allows_answer_reveal": False,
        },
    },
}

_EVALUATION_BINDING_ID = "binding.concept_recall.v1"
_PEDAGOGICAL_GOAL = "independent_concept_recall"


def _is_draft_field(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and "value" in payload
        and "provenance" in payload
        and "review_required" in payload
    )


def _unwrap_payload(payload: Any) -> Any:
    if _is_draft_field(payload):
        return _unwrap_payload(payload["value"])
    if isinstance(payload, dict):
        return {key: _unwrap_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_unwrap_payload(value) for value in payload]
    return payload


def _required_non_empty_string(
    payload: dict[str, Any],
    field_name: str,
    topic_slug: str,
    concept_index: int,
) -> str:
    value = _unwrap_payload(payload.get(field_name))
    if isinstance(value, str) and value:
        return value
    raise ExecutableLearningUnitMaterializationError(
        "concept field '{0}' must be a non-empty string for topic '{1}' concept index {2}".format(
            field_name,
            topic_slug,
            concept_index,
        )
    )


def _optional_non_empty_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = _unwrap_payload(payload.get(field_name))
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    return normalized or None


def _optional_non_empty_string_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = _unwrap_payload(payload.get(field_name))
    if isinstance(value, str):
        normalized = " ".join(value.split())
        return [normalized] if normalized else []
    if not isinstance(value, list):
        return []
    normalized_items = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = " ".join(item.split())
        if normalized:
            normalized_items.append(normalized)
    return normalized_items


def _candidate_card_types(topic_package: dict[str, Any]) -> list[str]:
    learning_design_drafts = topic_package.get("learning_design_drafts", {})
    candidate_card_types = learning_design_drafts.get("candidate_card_types", [])
    if not isinstance(candidate_card_types, list):
        raise ExecutableLearningUnitMaterializationError(
            "learning_design_drafts.candidate_card_types must be a list"
        )
    return candidate_card_types


def _unit_policy(mode: str, session_intent: str) -> dict[str, Any]:
    policy = _SUPPORTED_UNIT_POLICIES.get((mode, session_intent))
    if policy is None:
        raise ExecutableLearningUnitMaterializationError(
            "unsupported concept_recall materialization for mode '{0}' "
            "and session_intent '{1}'".format(mode, session_intent)
        )
    return policy


def _ensure_terminal_punctuation(text: str) -> str:
    if text[-1] in ".!?":
        return text
    return "{0}.".format(text)


def _build_study_visible_prompt(concept_title: str) -> str:
    return (
        "Explain the concept '{0}'. Cover what it is, when to use it, and "
        "the main trade-offs.".format(concept_title)
    )


def _build_practice_visible_prompt(concept: dict[str, Any], concept_title: str) -> str:
    prompt_parts = [
        "You're advising a teammate on whether to use '{0}' in a real system discussion.".format(
            concept_title
        )
    ]
    description = _optional_non_empty_string(concept, "description")
    if description is not None:
        prompt_parts.append("Context: {0}".format(_ensure_terminal_punctuation(description)))
    why_it_matters = _optional_non_empty_string_list(concept, "why_it_matters")
    if why_it_matters:
        prompt_parts.append(
            "Why it matters: {0}".format(_ensure_terminal_punctuation("; ".join(why_it_matters)))
        )
    when_to_use = _optional_non_empty_string_list(concept, "when_to_use")
    if when_to_use:
        prompt_parts.append(
            "Use-case cues: {0}".format(_ensure_terminal_punctuation("; ".join(when_to_use)))
        )
    tradeoffs = _optional_non_empty_string_list(concept, "tradeoffs")
    if tradeoffs:
        prompt_parts.append(
            "Trade-off cues: {0}".format(_ensure_terminal_punctuation("; ".join(tradeoffs)))
        )
    prompt_parts.append(
        "Explain what it is, when you would use it, and the main trade-offs you would call out."
    )
    return " ".join(prompt_parts)


def _build_visible_prompt(
    mode: str,
    concept: dict[str, Any],
    concept_title: str,
) -> str:
    if mode == "Practice":
        return _build_practice_visible_prompt(concept, concept_title)
    return _build_study_visible_prompt(concept_title)


def materialize_executable_learning_units(
    catalog: dict[str, dict[str, Any]],
    mode: str,
    session_intent: str,
) -> list[dict[str, Any]]:
    policy = _unit_policy(mode, session_intent)
    units = []

    for topic_slug in sorted(catalog):
        bundle = catalog[topic_slug]
        topic_package = bundle["topic_package"]
        if "recall" not in _candidate_card_types(topic_package):
            continue

        concepts = topic_package.get("canonical_content", {}).get("concepts", [])
        if not concepts:
            continue

        for concept_index, concept in enumerate(concepts):
            concept_id = _required_non_empty_string(concept, "id", topic_slug, concept_index)
            concept_title = _required_non_empty_string(concept, "title", topic_slug, concept_index)
            units.append(
                {
                    "id": "elu.concept_recall.{0}.{1}.{2}".format(
                        mode.lower(),
                        session_intent.replace("Review", "_review").replace("New", "_new").lower(),
                        concept_id,
                    ),
                    "source_content_ids": [concept_id],
                    "mode": mode,
                    "session_intent": session_intent,
                    "visible_prompt": _build_visible_prompt(mode, concept, concept_title),
                    "pedagogical_goal": _PEDAGOGICAL_GOAL,
                    "effective_difficulty": policy["effective_difficulty"],
                    "allowed_hint_levels": list(policy["allowed_hint_levels"]),
                    "follow_up_envelope": dict(policy["follow_up_envelope"]),
                    "completion_rules": dict(policy["completion_rules"]),
                    "evaluation_binding_id": _EVALUATION_BINDING_ID,
                }
            )

    return units


def supported_materialization_pairs() -> list[tuple[str, str]]:
    return sorted(_SUPPORTED_UNIT_POLICIES)
