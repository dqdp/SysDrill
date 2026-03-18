from typing import Any


def _is_draft_field(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and "value" in payload
        and "provenance" in payload
        and "review_required" in payload
    )


def _project_payload(payload: Any) -> Any:
    if _is_draft_field(payload):
        return _project_payload(payload["value"])
    if isinstance(payload, dict):
        return {key: _project_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_project_payload(value) for value in payload]
    return payload


def _draft_field_value(payload: Any) -> Any:
    if _is_draft_field(payload):
        return payload["value"]
    return payload


def _display_title_from_topic_package(topic_package: dict[str, Any]) -> str:
    canonical_content = topic_package.get("canonical_content", {})
    concepts = canonical_content.get("concepts", [])
    if concepts:
        title = _draft_field_value(concepts[0].get("title"))
        if isinstance(title, str) and title:
            return title

    scenarios = canonical_content.get("scenarios", [])
    if scenarios:
        title = _draft_field_value(scenarios[0].get("title"))
        if isinstance(title, str) and title:
            return title

    return topic_package["topic_slug"]


def build_topic_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    topic_package = bundle["topic_package"]
    canonical_content = topic_package.get("canonical_content", {})

    return {
        "topic_slug": topic_package["topic_slug"],
        "display_title": _display_title_from_topic_package(topic_package),
        "concept_count": len(canonical_content.get("concepts", [])),
        "pattern_count": len(canonical_content.get("patterns", [])),
        "scenario_count": len(canonical_content.get("scenarios", [])),
        "review_status": topic_package.get("review", {}).get("status"),
        "schema_valid": topic_package.get("validation_summary", {}).get("schema_valid", False),
    }


def build_topic_detail(bundle: dict[str, Any]) -> dict[str, Any]:
    topic_package = bundle["topic_package"]
    validation_summary = topic_package.get("validation_summary") or {
        "schema_valid": bundle["validation_report"].get("schema_valid", False),
        "errors": bundle["validation_report"].get("errors", []),
        "warnings": bundle["validation_report"].get("warnings", []),
    }

    return {
        "topic_slug": topic_package["topic_slug"],
        "bundle_source_name": bundle["bundle_source_name"],
        "is_draft_bundle": bundle["is_draft_bundle"],
        "source_document_ids": topic_package.get("source_document_ids", []),
        "canonical_content": _project_payload(topic_package.get("canonical_content", {})),
        "canonical_support": _project_payload(topic_package.get("canonical_support", {})),
        "review": topic_package.get("review", {}),
        "validation_summary": validation_summary,
    }
