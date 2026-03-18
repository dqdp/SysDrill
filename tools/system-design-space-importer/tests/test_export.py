import copy
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from system_design_space_importer.cli import main


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


if __name__ == "__main__":
    unittest.main()
