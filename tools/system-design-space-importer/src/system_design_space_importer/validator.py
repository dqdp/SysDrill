from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.utils import utc_now_iso


def _collect_low_confidence_paths(payload, prefix=""):
    paths = []
    if isinstance(payload, dict):
        if "review_required" in payload and "provenance" in payload:
            confidence_values = [ref.get("confidence", 0.0) for ref in payload["provenance"]]
            is_low_confidence = any(value < 0.7 for value in confidence_values)
            if payload.get("review_required") or is_low_confidence:
                paths.append(prefix.rstrip("."))
        for key, value in payload.items():
            child_prefix = "{0}{1}.".format(prefix, key)
            paths.extend(_collect_low_confidence_paths(value, child_prefix))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            child_prefix = "{0}[{1}].".format(prefix.rstrip("."), index)
            paths.extend(_collect_low_confidence_paths(value, child_prefix))
    return paths


def validate_semantic_draft(draft):
    errors = []
    warnings = list(draft.get("warnings", []))

    required_fields = (
        "draft_id",
        "source_document_ids",
        "inferred_topic_slug",
        "mapper_version",
        "concepts",
    )
    for field in required_fields:
        if field not in draft:
            errors.append("missing required field: {0}".format(field))

    if not draft.get("concepts"):
        errors.append("at least one concept draft is required in scaffold mode")

    if not draft.get("hint_ladders"):
        warnings.append("no hint ladders were generated")

    low_confidence_paths = sorted(set(_collect_low_confidence_paths(draft)))

    return {
        "package_id": "topicpkg.{0}".format(draft.get("inferred_topic_slug", "unknown")),
        "checked_at": utc_now_iso(),
        "schema_valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "low_confidence_paths": low_confidence_paths,
        "missing_required_paths": [],
    }


def run_validate(layout):
    layout.ensure_base()
    reports = {}
    for draft_path in layout.drafts_dir.glob("*/semantic-draft.json"):
        draft = read_json(draft_path)
        report = validate_semantic_draft(draft)
        output_path = layout.reports_dir / draft["inferred_topic_slug"] / "validation-report.json"
        write_json(output_path, report)
        reports[draft["inferred_topic_slug"]] = report
    return reports
