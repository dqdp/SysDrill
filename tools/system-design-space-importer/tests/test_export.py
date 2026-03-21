import copy
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from system_design_space_importer.cli import main
from system_design_space_importer.jsonio import write_json
from system_design_space_importer.packager import run_export, run_package
from system_design_space_importer.paths import RunLayout


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _normalize_package(payload):
    normalized = copy.deepcopy(payload)
    normalized["generated_at"] = "<generated_at>"
    return normalized


class ExportMaterializeTest(unittest.TestCase):
    def setUp(self):
        self.fixture = (
            Path(__file__).parent / "fixtures" / "raw_html" / "event-driven-architecture.html"
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "out"
        self.expected_package = _load_json(
            Path(__file__).parent / "fixtures" / "expected" / "exported-topic-package.snapshot.json"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_stage(self, *argv):
        return main(list(argv) + ["--out-dir", str(self.out_dir), "--run-id", self.run_id])

    def test_export_stage_materializes_expected_output_tree(self):
        self.run_id = "export-run"

        self.assertEqual(
            self._run_stage(
                "discover",
                "--seed",
                self.fixture.resolve().as_uri(),
            ),
            0,
        )
        self.assertEqual(self._run_stage("fetch"), 0)
        self.assertEqual(self._run_stage("extract"), 0)
        self.assertEqual(self._run_stage("map"), 0)
        self.assertEqual(self._run_stage("validate"), 0)
        self.assertEqual(self._run_stage("package"), 0)
        self.assertEqual(self._run_stage("export"), 0)

        export_dir = self.out_dir / "exports" / "system-design-space" / "event-driven-architecture"
        self.assertTrue((export_dir / "topic-package.yaml").exists())
        self.assertTrue((export_dir / "provenance.json").exists())
        self.assertTrue((export_dir / "validation-report.json").exists())

        package = _load_yaml(export_dir / "topic-package.yaml")
        self.assertEqual(_normalize_package(package), self.expected_package)

        provenance = _load_json(export_dir / "provenance.json")
        self.assertEqual(provenance["topic_slug"], "event-driven-architecture")
        self.assertEqual(provenance["run_id"], self.run_id)
        self.assertEqual(provenance["source_name"], "system-design.space")
        self.assertEqual(provenance["source_document_ids"], ["event-driven-architecture"])
        self.assertEqual(
            provenance["artifacts"]["draft_topic_package_path"],
            "runs/export-run/packages/event-driven-architecture/draft-topic-package.json",
        )
        self.assertTrue(provenance["documents"][0]["source_url"].startswith("file://"))

        report = _load_json(export_dir / "validation-report.json")
        self.assertTrue(report["schema_valid"])
        self.assertTrue(report["low_confidence_paths"])

    def test_run_pipeline_includes_export_stage(self):
        self.run_id = "full-run"

        result = main(
            [
                "run",
                "--seed",
                self.fixture.resolve().as_uri(),
                "--out-dir",
                str(self.out_dir),
                "--run-id",
                self.run_id,
            ]
        )

        self.assertEqual(result, 0)
        export_path = (
            self.out_dir
            / "exports"
            / "system-design-space"
            / "event-driven-architecture"
            / "topic-package.yaml"
        )
        self.assertTrue(export_path.exists())

    def test_export_fails_closed_for_invalid_validation_report(self):
        self.run_id = "invalid-run"

        self.assertEqual(
            self._run_stage(
                "discover",
                "--seed",
                self.fixture.resolve().as_uri(),
            ),
            0,
        )
        self.assertEqual(self._run_stage("fetch"), 0)
        self.assertEqual(self._run_stage("extract"), 0)
        self.assertEqual(self._run_stage("map"), 0)
        self.assertEqual(self._run_stage("validate"), 0)
        self.assertEqual(self._run_stage("package"), 0)

        report_path = (
            self.out_dir
            / "runs"
            / self.run_id
            / "reports"
            / "event-driven-architecture"
            / "validation-report.json"
        )
        report = _load_json(report_path)
        report["schema_valid"] = False
        report["errors"] = ["forced invalid report"]
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "schema_valid"):
            self._run_stage("export")

        export_dir = self.out_dir / "exports" / "system-design-space" / "event-driven-architecture"
        self.assertFalse(export_dir.exists())

    def test_export_preserves_seeded_scenarios_when_present(self):
        layout = RunLayout(out_dir=self.out_dir, run_id="scenario-export")
        layout.ensure_base()

        draft = {
            "draft_id": "semdraft.troubleshooting-example",
            "source_document_ids": ["troubleshooting-example"],
            "inferred_topic_slug": "troubleshooting-example",
            "mapper_version": "0.1.0",
            "concepts": [
                {
                    "id": {
                        "value": "concept.troubleshooting-example",
                        "provenance": [],
                        "review_required": False,
                    },
                    "title": {
                        "value": "Пример Troubleshooting Interview",
                        "provenance": [],
                        "review_required": False,
                    },
                    "description": {
                        "value": "Разбор troubleshooting-кейса.",
                        "provenance": [],
                        "review_required": False,
                    },
                    "why_it_matters": {"value": [], "provenance": [], "review_required": True},
                    "when_to_use": {"value": [], "provenance": [], "review_required": True},
                    "tradeoffs": {"value": [], "provenance": [], "review_required": True},
                    "related_concepts": {"value": [], "provenance": [], "review_required": True},
                    "prerequisites": {"value": [], "provenance": [], "review_required": True},
                }
            ],
            "patterns": [],
            "scenarios": [
                {
                    "id": {
                        "value": "scenario.troubleshooting-example",
                        "provenance": [],
                        "review_required": False,
                    },
                    "title": {
                        "value": "Пример Troubleshooting Interview",
                        "provenance": [],
                        "review_required": False,
                    },
                    "prompt": {
                        "value": (
                            "Разберите incident со снижением платежей и объясните ход диагностики."
                        ),
                        "provenance": [],
                        "review_required": True,
                    },
                    "content_difficulty_baseline": {
                        "value": "standard",
                        "provenance": [],
                        "review_required": True,
                    },
                    "expected_focus_areas": {
                        "value": ["Архитектурный контекст", "Диагностика инцидента"],
                        "provenance": [],
                        "review_required": True,
                    },
                    "canonical_axes": {
                        "value": [
                            "Методология диагностики — системный подход vs хаотичный поиск",
                            "Формулирование гипотез и их проверка",
                        ],
                        "provenance": [],
                        "review_required": True,
                    },
                    "canonical_follow_up_candidates": {
                        "value": [
                            "Уточнить архитектуру платёжного потока",
                            "Разобрать workaround и полноценное исправление",
                        ],
                        "provenance": [],
                        "review_required": True,
                    },
                }
            ],
            "hint_ladders": [],
            "unresolved_fragment_ids": [],
            "warnings": [],
        }
        report = {
            "package_id": "topicpkg.troubleshooting-example",
            "checked_at": "2026-03-20T00:00:00+00:00",
            "schema_valid": True,
            "errors": [],
            "warnings": [],
            "low_confidence_paths": ["scenarios[0].prompt"],
            "missing_required_paths": [],
        }
        manifest = {
            "seed": "file:///tmp/troubleshooting-example.html",
            "profile": "chapters_only",
            "fetch_policy": {"allowed_sources": ["file"]},
            "discovery_policy": {},
            "robots_policy": {},
        }
        source_document = {
            "document_id": "troubleshooting-example",
            "source_name": "system-design.space",
            "source_url": "file:///tmp/troubleshooting-example.html",
            "fetched_at": "2026-03-20T00:00:00+00:00",
            "fetch_mode": "file_copy",
            "http_status": 200,
            "content_type": "text/html",
            "source_hash": "sha256:test",
            "raw_html_path": "runs/scenario-export/documents/troubleshooting-example/raw.html",
            "normalized_text_path": (
                "runs/scenario-export/documents/troubleshooting-example/normalized.txt"
            ),
            "parser_version": "0.1.0",
        }

        write_json(layout.manifest_path, manifest)
        write_json(
            layout.documents_dir / "troubleshooting-example" / "source_document.json",
            source_document,
        )
        write_json(
            layout.drafts_dir / "troubleshooting-example" / "semantic-draft.json",
            draft,
        )
        write_json(
            layout.reports_dir / "troubleshooting-example" / "validation-report.json",
            report,
        )

        packages = run_package(layout)
        self.assertIn("troubleshooting-example", packages)

        exports = run_export(layout)
        self.assertIn("troubleshooting-example", exports)

        package = _load_yaml(
            self.out_dir
            / "exports"
            / "system-design-space"
            / "troubleshooting-example"
            / "topic-package.yaml"
        )
        self.assertEqual(
            package["canonical_content"]["scenarios"][0]["id"]["value"],
            "scenario.troubleshooting-example",
        )
        self.assertEqual(
            package["canonical_content"]["scenarios"][0]["content_difficulty_baseline"]["value"],
            "standard",
        )
        self.assertEqual(
            package["canonical_content"]["scenarios"][0]["canonical_axes"]["value"],
            [
                "Методология диагностики — системный подход vs хаотичный поиск",
                "Формулирование гипотез и их проверка",
            ],
        )


if __name__ == "__main__":
    unittest.main()
