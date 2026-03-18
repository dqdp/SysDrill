import tempfile
import unittest
from pathlib import Path

import yaml

from system_design_space_importer.cli import main


class ImporterFixturePipelineSmokeTest(unittest.TestCase):
    def test_run_command_materializes_export_bundle_from_fixture_seed(self):
        fixture = Path(__file__).parent / "fixtures" / "raw_html" / "event-driven-architecture.html"

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "out"
            result = main(
                [
                    "run",
                    "--seed",
                    fixture.resolve().as_uri(),
                    "--out-dir",
                    str(out_dir),
                    "--run-id",
                    "smoke-run",
                ]
            )

            self.assertEqual(result, 0)

            export_dir = out_dir / "exports" / "system-design-space" / "event-driven-architecture"
            self.assertTrue((export_dir / "topic-package.yaml").exists())
            self.assertTrue((export_dir / "provenance.json").exists())
            self.assertTrue((export_dir / "validation-report.json").exists())

            with (export_dir / "topic-package.yaml").open("r", encoding="utf-8") as handle:
                package = yaml.safe_load(handle)

            self.assertEqual(package["topic_slug"], "event-driven-architecture")
            self.assertEqual(
                package["learning_design_drafts"]["candidate_card_types"],
                ["recall"],
            )
            self.assertIn("canonical_content", package)
            self.assertIn("review", package)


if __name__ == "__main__":
    unittest.main()
