import json
import shutil
import tempfile
import unittest
from pathlib import Path

from sysdrill_backend.content_bundle_reader import BundleLoadError, load_topic_catalog


class ContentBundleReaderTest(unittest.TestCase):
    def setUp(self):
        self.fixture_root = Path(__file__).parent / "fixtures" / "export_root"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_root = Path(self.temp_dir.name) / "exports"
        shutil.copytree(self.fixture_root, self.export_root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_loads_valid_bundles_in_sorted_topic_order(self):
        catalog = load_topic_catalog(self.export_root, allow_draft_bundles=True)

        self.assertEqual(list(catalog), ["alpha-topic", "zeta-topic"])
        self.assertEqual(
            catalog["alpha-topic"]["topic_package"]["canonical_content"]["concepts"][0]["title"][
                "value"
            ],
            "Кэширование",
        )
        self.assertEqual(catalog["alpha-topic"]["validation_report"]["schema_valid"], True)
        self.assertEqual(catalog["alpha-topic"]["provenance"]["topic_slug"], "alpha-topic")
        self.assertEqual(catalog["alpha-topic"]["bundle_source_name"], "system-design-space")
        self.assertTrue(catalog["alpha-topic"]["is_draft_bundle"])

    def test_rejects_draft_bundle_loading_when_explicit_mode_is_disabled(self):
        with self.assertRaisesRegex(BundleLoadError, "allow_draft_bundles"):
            load_topic_catalog(self.export_root, allow_draft_bundles=False)

    def test_rejects_missing_topic_package(self):
        (self.export_root / "system-design-space" / "alpha-topic" / "topic-package.yaml").unlink()

        with self.assertRaisesRegex(BundleLoadError, "topic-package.yaml"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_missing_validation_report(self):
        (
            self.export_root / "system-design-space" / "alpha-topic" / "validation-report.json"
        ).unlink()

        with self.assertRaisesRegex(BundleLoadError, "validation-report.json"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_missing_provenance(self):
        (self.export_root / "system-design-space" / "alpha-topic" / "provenance.json").unlink()

        with self.assertRaisesRegex(BundleLoadError, "provenance.json"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_invalid_validation_report(self):
        report_path = (
            self.export_root / "system-design-space" / "alpha-topic" / "validation-report.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["schema_valid"] = False
        report["errors"] = ["forced invalid report"]
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(BundleLoadError, "schema_valid"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_topic_slug_directory_mismatch(self):
        package_path = (
            self.export_root / "system-design-space" / "alpha-topic" / "topic-package.yaml"
        )
        package_text = package_path.read_text(encoding="utf-8").replace(
            "topic_slug: alpha-topic",
            "topic_slug: wrong-slug",
        )
        package_path.write_text(package_text, encoding="utf-8")

        with self.assertRaisesRegex(BundleLoadError, "topic_slug"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_export_root_when_no_topic_bundles_are_found(self):
        empty_root = Path(self.temp_dir.name) / "empty-export-root"
        (empty_root / "system-design-space").mkdir(parents=True)

        with self.assertRaisesRegex(BundleLoadError, "topic bundles"):
            load_topic_catalog(empty_root, allow_draft_bundles=True)

    def test_rejects_symlinked_source_directory(self):
        symlink_root = Path(self.temp_dir.name) / "symlink-export-root"
        symlink_root.mkdir()
        (symlink_root / "system-design-space").symlink_to(
            self.export_root / "system-design-space",
            target_is_directory=True,
        )

        with self.assertRaisesRegex(BundleLoadError, "symlink"):
            load_topic_catalog(symlink_root, allow_draft_bundles=True)

    def test_rejects_symlinked_topic_directory(self):
        symlink_root = Path(self.temp_dir.name) / "topic-symlink-export-root"
        source_dir = symlink_root / "system-design-space"
        source_dir.mkdir(parents=True)
        (source_dir / "alpha-topic").symlink_to(
            self.export_root / "system-design-space" / "alpha-topic",
            target_is_directory=True,
        )

        with self.assertRaisesRegex(BundleLoadError, "symlink"):
            load_topic_catalog(symlink_root, allow_draft_bundles=True)

    def test_rejects_topic_package_when_yaml_payload_is_not_mapping(self):
        package_path = (
            self.export_root / "system-design-space" / "alpha-topic" / "topic-package.yaml"
        )
        package_path.write_text("- bad\n", encoding="utf-8")

        with self.assertRaisesRegex(BundleLoadError, "topic-package.yaml"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_provenance_when_json_payload_is_not_object(self):
        provenance_path = (
            self.export_root / "system-design-space" / "alpha-topic" / "provenance.json"
        )
        provenance_path.write_text("[]\n", encoding="utf-8")

        with self.assertRaisesRegex(BundleLoadError, "provenance.json"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_validation_report_when_json_payload_is_not_object(self):
        report_path = (
            self.export_root / "system-design-space" / "alpha-topic" / "validation-report.json"
        )
        report_path.write_text("[]\n", encoding="utf-8")

        with self.assertRaisesRegex(BundleLoadError, "validation-report.json"):
            load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_rejects_export_root_escape(self):
        with self.assertRaisesRegex(BundleLoadError, "export root"):
            load_topic_catalog(self.export_root / "..", allow_draft_bundles=True)


if __name__ == "__main__":
    unittest.main()
