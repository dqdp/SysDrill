from typing import Any


class ExecutableLearningUnitMaterializationError(ValueError):
    pass


_CONCEPT_RECALL_POLICIES: dict[tuple[str, str], dict[str, Any]] = {
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

_SCENARIO_READINESS_PAIR = ("MockInterview", "ReadinessCheck")
_SCENARIO_READINESS_POLICY = {
    "allowed_hint_levels": [1],
    "follow_up_envelope": {
        "max_follow_ups": 1,
        "follow_up_style": "bounded_probe",
    },
    "completion_rules": {
        "submission_kind": "manual_submit",
        "answer_boundary": "bounded_follow_up",
        "allows_answer_reveal": False,
    },
}

_CONCEPT_RECALL_EVALUATION_BINDING_ID = "binding.concept_recall.v1"
_CONCEPT_RECALL_PEDAGOGICAL_GOAL = "independent_concept_recall"
_SCENARIO_READINESS_UNIT_FAMILY = "scenario_readiness_check"
_SCENARIO_READINESS_PEDAGOGICAL_GOAL = "bounded_mock_readiness_check"
_SCENARIO_BINDINGS = {
    "scenario.rate-limiter.basic": {
        "scenario_family": "rate_limiter",
        "evaluation_binding_id": "binding.rate_limiter.v1",
    },
    "scenario.url-shortener.basic": {
        "scenario_family": "url_shortener",
        "evaluation_binding_id": "binding.url_shortener.v1",
    },
}


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
    record_index: int,
    record_kind: str = "concept",
) -> str:
    value = _unwrap_payload(payload.get(field_name))
    if isinstance(value, str) and value:
        return value
    raise ExecutableLearningUnitMaterializationError(
        "{0} field '{1}' must be a non-empty string for topic '{2}' {0} index {3}".format(
            record_kind,
            field_name,
            topic_slug,
            record_index,
        )
    )


def _required_non_empty_string_list(
    payload: dict[str, Any],
    field_name: str,
    topic_slug: str,
    record_index: int,
    record_kind: str,
) -> list[str]:
    values = _optional_non_empty_string_list(payload, field_name)
    if values:
        return values
    raise ExecutableLearningUnitMaterializationError(
        "{0} field '{1}' must be a non-empty string list for topic '{2}' {0} index {3}".format(
            record_kind,
            field_name,
            topic_slug,
            record_index,
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


def _concept_recall_policy(mode: str, session_intent: str) -> dict[str, Any]:
    policy = _CONCEPT_RECALL_POLICIES.get((mode, session_intent))
    if policy is None:
        raise ExecutableLearningUnitMaterializationError(
            "unsupported concept_recall materialization for mode '{0}' "
            "and session_intent '{1}'".format(mode, session_intent)
        )
    return policy


def _supported_mock_pair(mode: str, session_intent: str) -> bool:
    return (mode, session_intent) == _SCENARIO_READINESS_PAIR


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


def _snake_case_token(value: str) -> str:
    token = []
    for index, character in enumerate(value):
        if character.isupper() and index > 0 and value[index - 1].islower():
            token.append("_")
        token.append(character.lower())
    return "".join(token)


def _concept_recall_unit_id(mode: str, session_intent: str, concept_id: str) -> str:
    return "elu.concept_recall.{0}.{1}.{2}".format(
        _snake_case_token(mode),
        _snake_case_token(session_intent),
        concept_id,
    )


def _scenario_readiness_unit_id(mode: str, session_intent: str, scenario_id: str) -> str:
    return "elu.{0}.{1}.{2}.{3}".format(
        _SCENARIO_READINESS_UNIT_FAMILY,
        _snake_case_token(mode),
        _snake_case_token(session_intent),
        scenario_id,
    )


def _scenario_binding_metadata(scenario_id: str) -> dict[str, str]:
    binding = _SCENARIO_BINDINGS.get(scenario_id)
    if binding is None:
        raise ExecutableLearningUnitMaterializationError(
            "unsupported scenario binding for scenario '{0}'".format(scenario_id)
        )
    return binding


def _catalog_concept_ids(catalog: dict[str, dict[str, Any]]) -> set[str]:
    concept_ids: set[str] = set()
    for bundle in catalog.values():
        topic_package = bundle.get("topic_package", {})
        canonical_content = topic_package.get("canonical_content")
        if not isinstance(canonical_content, dict):
            continue
        concepts = canonical_content.get("concepts", [])
        if not isinstance(concepts, list):
            continue
        for concept in concepts:
            if not isinstance(concept, dict):
                continue
            concept_id = _optional_non_empty_string(concept, "id")
            if concept_id is not None:
                concept_ids.add(concept_id)
    return concept_ids


def _validated_bound_concept_ids(
    scenario: dict[str, Any],
    topic_slug: str,
    scenario_index: int,
    known_concept_ids: set[str],
) -> list[str]:
    bound_concept_ids = _optional_non_empty_string_list(scenario, "bound_concept_ids")
    unknown_concept_ids = [
        concept_id for concept_id in bound_concept_ids if concept_id not in known_concept_ids
    ]
    if unknown_concept_ids:
        raise ExecutableLearningUnitMaterializationError(
            "scenario field 'bound_concept_ids' contains unknown concept id(s) {0} "
            "for topic '{1}' scenario index {2}".format(
                sorted(unknown_concept_ids),
                topic_slug,
                scenario_index,
            )
        )
    return bound_concept_ids


def _materialize_concept_recall_units(
    catalog: dict[str, dict[str, Any]],
    mode: str,
    session_intent: str,
) -> list[dict[str, Any]]:
    policy = _concept_recall_policy(mode, session_intent)
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
                    "id": _concept_recall_unit_id(mode, session_intent, concept_id),
                    "source_content_ids": [concept_id],
                    "mode": mode,
                    "session_intent": session_intent,
                    "visible_prompt": _build_visible_prompt(mode, concept, concept_title),
                    "pedagogical_goal": _CONCEPT_RECALL_PEDAGOGICAL_GOAL,
                    "effective_difficulty": policy["effective_difficulty"],
                    "allowed_hint_levels": list(policy["allowed_hint_levels"]),
                    "follow_up_envelope": dict(policy["follow_up_envelope"]),
                    "completion_rules": dict(policy["completion_rules"]),
                    "evaluation_binding_id": _CONCEPT_RECALL_EVALUATION_BINDING_ID,
                }
            )

    return units


def _materialize_scenario_readiness_units(
    catalog: dict[str, dict[str, Any]],
    mode: str,
    session_intent: str,
) -> list[dict[str, Any]]:
    units = []
    known_concept_ids = _catalog_concept_ids(catalog)

    for topic_slug in sorted(catalog):
        bundle = catalog[topic_slug]
        topic_package = bundle["topic_package"]
        if "mini_scenario" not in _candidate_card_types(topic_package):
            continue

        scenarios = topic_package.get("canonical_content", {}).get("scenarios", [])
        if not scenarios:
            continue

        for scenario_index, scenario in enumerate(scenarios):
            scenario_id = _required_non_empty_string(
                scenario,
                "id",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            _required_non_empty_string(
                scenario,
                "title",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            scenario_title = _required_non_empty_string(
                scenario,
                "title",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            scenario_prompt = _required_non_empty_string(
                scenario,
                "prompt",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            effective_difficulty = _required_non_empty_string(
                scenario,
                "content_difficulty_baseline",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            _required_non_empty_string_list(
                scenario,
                "expected_focus_areas",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            _required_non_empty_string_list(
                scenario,
                "canonical_axes",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            canonical_follow_up_candidates = _required_non_empty_string_list(
                scenario,
                "canonical_follow_up_candidates",
                topic_slug,
                scenario_index,
                record_kind="scenario",
            )
            bound_concept_ids = _validated_bound_concept_ids(
                scenario,
                topic_slug,
                scenario_index,
                known_concept_ids,
            )
            binding = _scenario_binding_metadata(scenario_id)
            unit = {
                "id": _scenario_readiness_unit_id(mode, session_intent, scenario_id),
                "source_content_ids": [scenario_id],
                "mode": mode,
                "session_intent": session_intent,
                "unit_family": _SCENARIO_READINESS_UNIT_FAMILY,
                "scenario_family": binding["scenario_family"],
                "scenario_title": scenario_title,
                "visible_prompt": scenario_prompt,
                "canonical_follow_up_candidates": canonical_follow_up_candidates,
                "pedagogical_goal": _SCENARIO_READINESS_PEDAGOGICAL_GOAL,
                "effective_difficulty": effective_difficulty,
                "allowed_hint_levels": list(_SCENARIO_READINESS_POLICY["allowed_hint_levels"]),
                "follow_up_envelope": dict(_SCENARIO_READINESS_POLICY["follow_up_envelope"]),
                "completion_rules": dict(_SCENARIO_READINESS_POLICY["completion_rules"]),
                "evaluation_binding_id": binding["evaluation_binding_id"],
            }
            if bound_concept_ids:
                unit["bound_concept_ids"] = bound_concept_ids
            units.append(unit)

    return units


def materialize_executable_learning_units(
    catalog: dict[str, dict[str, Any]],
    mode: str,
    session_intent: str,
) -> list[dict[str, Any]]:
    if _supported_mock_pair(mode, session_intent):
        return _materialize_scenario_readiness_units(catalog, mode, session_intent)
    return _materialize_concept_recall_units(catalog, mode, session_intent)


def supported_materialization_pairs() -> list[tuple[str, str]]:
    return sorted(list(_CONCEPT_RECALL_POLICIES) + [_SCENARIO_READINESS_PAIR])
