from pathlib import Path

from system_design_space_importer import __version__
from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.utils import utc_now_iso
from system_design_space_importer.yamlio import write_yaml


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


def _relative_to_out_dir(layout, path):
    return str(Path(path).resolve().relative_to(layout.out_dir.resolve()))


def _export_source_dir_name(source_name):
    return source_name.replace(".", "-")


def build_provenance(layout, manifest, package, documents):
    topic_slug = package["topic_slug"]
    source_name = documents[0]["source_name"] if documents else "system-design.space"
    source_document_ids = [document["document_id"] for document in documents]
    fragments_paths = [
        _relative_to_out_dir(layout, layout.fragments_dir / document_id / "fragments.json")
        for document_id in source_document_ids
    ]

    return {
        "package_id": package["package_id"],
        "topic_slug": topic_slug,
        "run_id": layout.run_id,
        "source_name": source_name,
        "source_document_ids": source_document_ids,
        "manifest": {
            "path": _relative_to_out_dir(layout, layout.manifest_path),
            "seed": manifest.get("seed"),
            "profile": manifest.get("profile"),
            "fetch_policy": manifest.get("fetch_policy"),
            "discovery_policy": manifest.get("discovery_policy"),
            "robots_policy": manifest.get("robots_policy"),
        },
        "documents": documents,
        "artifacts": {
            "semantic_draft_path": _relative_to_out_dir(
                layout,
                layout.drafts_dir / topic_slug / "semantic-draft.json",
            ),
            "validation_report_path": _relative_to_out_dir(
                layout,
                layout.reports_dir / topic_slug / "validation-report.json",
            ),
            "draft_topic_package_path": _relative_to_out_dir(
                layout,
                layout.packages_dir / topic_slug / "draft-topic-package.json",
            ),
            "fragments_paths": fragments_paths,
        },
    }


def run_export(layout):
    layout.ensure_base()
    manifest = read_json(layout.manifest_path)
    exports = {}

    for package_path in layout.packages_dir.glob("*/draft-topic-package.json"):
        topic_slug = package_path.parent.name
        report_path = layout.reports_dir / topic_slug / "validation-report.json"
        report = read_json(report_path)
        if not report.get("schema_valid", False):
            raise ValueError(
                "cannot export package for topic '{0}': schema_valid is false".format(topic_slug)
            )

        package = read_json(package_path)
        documents = []
        for document_id in package.get("source_document_ids", []):
            source_document_path = layout.documents_dir / document_id / "source_document.json"
            documents.append(read_json(source_document_path))

        provenance = build_provenance(layout, manifest, package, documents)
        source_dir_name = _export_source_dir_name(provenance["source_name"])
        export_dir = layout.exports_dir / source_dir_name / topic_slug

        write_yaml(export_dir / "topic-package.yaml", package)
        write_json(export_dir / "provenance.json", provenance)
        write_json(export_dir / "validation-report.json", report)

        exports[topic_slug] = {
            "topic_package_path": str(export_dir / "topic-package.yaml"),
            "provenance_path": str(export_dir / "provenance.json"),
            "validation_report_path": str(export_dir / "validation-report.json"),
        }

    return exports
