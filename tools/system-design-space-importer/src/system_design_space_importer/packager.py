from system_design_space_importer import __version__
from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.utils import utc_now_iso


def build_package(draft, report):
    required_actions = []
    for warning in report.get("warnings", []):
        required_actions.append(warning)
    for path in report.get("low_confidence_paths", []):
        required_actions.append("review low-confidence field: {0}".format(path))

    package = {
        "package_id": report["package_id"],
        "topic_slug": draft["inferred_topic_slug"],
        "generated_at": utc_now_iso(),
        "tool_version": __version__,
        "source_document_ids": draft["source_document_ids"],
        "canonical_content": {
            "concepts": draft["concepts"],
            "patterns": draft["patterns"],
            "scenarios": draft["scenarios"],
        },
        "canonical_support": {
            "hint_ladders": draft["hint_ladders"],
        },
        "learning_design_drafts": {
            "coverage_notes": [
                "derive at least one recall card after editorial approval",
                "defer learning-design expansion until canonical content is reviewed",
            ],
            "candidate_card_types": ["recall"],
        },
        "review": {
            "status": "needs_review" if required_actions else "approved",
            "required_actions": required_actions,
        },
        "validation_summary": {
            "schema_valid": report["schema_valid"],
            "errors": report["errors"],
            "warnings": report["warnings"],
        },
    }
    return package


def run_package(layout):
    layout.ensure_base()
    packages = {}
    for draft_path in layout.drafts_dir.glob("*/semantic-draft.json"):
        topic_slug = draft_path.parent.name
        report_path = layout.reports_dir / topic_slug / "validation-report.json"
        draft = read_json(draft_path)
        report = read_json(report_path)
        package = build_package(draft, report)
        output_path = layout.packages_dir / topic_slug / "draft-topic-package.json"
        write_json(output_path, package)
        packages[topic_slug] = package
    return packages
