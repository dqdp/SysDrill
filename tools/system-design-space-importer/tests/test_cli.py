import json
import tempfile
import unittest
from pathlib import Path

from system_design_space_importer.cli import main


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class CliPipelineTest(unittest.TestCase):
    def setUp(self):
        self.fixture = (
            Path(__file__).parent / "fixtures" / "raw_html" / "event-driven-architecture.html"
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "out"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_pipeline_creates_expected_artifacts(self):
        run_id = "test-run"

        result = main(
            [
                "run",
                "--seed",
                self.fixture.resolve().as_uri(),
                "--out-dir",
                str(self.out_dir),
                "--run-id",
                run_id,
            ]
        )

        self.assertEqual(result, 0)

        base_dir = self.out_dir / "runs" / run_id
        self.assertTrue((base_dir / "manifest.json").exists())
        self.assertTrue(
            (base_dir / "documents" / "event-driven-architecture" / "source_document.json").exists()
        )
        self.assertTrue(
            (base_dir / "fragments" / "event-driven-architecture" / "fragments.json").exists()
        )
        self.assertTrue(
            (base_dir / "drafts" / "event-driven-architecture" / "semantic-draft.json").exists()
        )
        self.assertTrue(
            (base_dir / "reports" / "event-driven-architecture" / "validation-report.json").exists()
        )
        self.assertTrue(
            (
                base_dir / "packages" / "event-driven-architecture" / "draft-topic-package.json"
            ).exists()
        )

        package = _load_json(
            base_dir / "packages" / "event-driven-architecture" / "draft-topic-package.json"
        )
        self.assertEqual(package["topic_slug"], "event-driven-architecture")
        self.assertEqual(package["review"]["status"], "needs_review")

    def test_sequential_stage_commands_produce_expected_content(self):
        run_id = "sequential-run"

        self.assertEqual(
            main(
                [
                    "discover",
                    "--seed",
                    self.fixture.resolve().as_uri(),
                    "--out-dir",
                    str(self.out_dir),
                    "--run-id",
                    run_id,
                ]
            ),
            0,
        )
        self.assertEqual(main(["fetch", "--out-dir", str(self.out_dir), "--run-id", run_id]), 0)
        self.assertEqual(main(["extract", "--out-dir", str(self.out_dir), "--run-id", run_id]), 0)
        self.assertEqual(main(["map", "--out-dir", str(self.out_dir), "--run-id", run_id]), 0)
        self.assertEqual(main(["validate", "--out-dir", str(self.out_dir), "--run-id", run_id]), 0)
        self.assertEqual(main(["package", "--out-dir", str(self.out_dir), "--run-id", run_id]), 0)

        base_dir = self.out_dir / "runs" / run_id
        fragments = _load_json(
            base_dir / "fragments" / "event-driven-architecture" / "fragments.json"
        )
        kinds = [fragment["kind"] for fragment in fragments]
        self.assertIn("title", kinds)
        self.assertIn("summary", kinds)
        self.assertIn("section_heading", kinds)

        report = _load_json(
            base_dir / "reports" / "event-driven-architecture" / "validation-report.json"
        )
        self.assertTrue(report["schema_valid"])
        self.assertTrue(report["low_confidence_paths"])

    def test_fetch_records_hash_and_paths_for_file_seed(self):
        run_id = "fetch-run"

        self.assertEqual(
            main(
                [
                    "discover",
                    "--seed",
                    self.fixture.resolve().as_uri(),
                    "--out-dir",
                    str(self.out_dir),
                    "--run-id",
                    run_id,
                ]
            ),
            0,
        )
        self.assertEqual(main(["fetch", "--out-dir", str(self.out_dir), "--run-id", run_id]), 0)

        source_document = _load_json(
            self.out_dir
            / "runs"
            / run_id
            / "documents"
            / "event-driven-architecture"
            / "source_document.json"
        )
        self.assertTrue(source_document["source_url"].startswith("file://"))
        self.assertTrue(source_document["source_hash"].startswith("sha256:"))
        self.assertTrue(source_document["raw_html_path"].endswith("raw.html"))
        self.assertTrue(source_document["normalized_text_path"].endswith("normalized.txt"))

    def test_pyproject_requires_python_3_12_or_newer(self):
        pyproject_text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn('requires-python = ">=3.12"', pyproject_text)


if __name__ == "__main__":
    unittest.main()
