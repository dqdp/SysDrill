import tempfile
import unittest
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app
from sysdrill_backend.content_bundle_reader import BundleLoadError


class ContentCatalogApiTest(unittest.TestCase):
    def setUp(self):
        self.export_root = Path(__file__).parent / "fixtures" / "export_root"

    def test_create_app_accepts_explicit_content_configuration(self):
        app = create_app(content_export_root=self.export_root, allow_draft_bundles=True)

        client = TestClient(app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_create_app_fails_closed_for_invalid_export_root(self):
        with self.assertRaisesRegex(BundleLoadError, "export root"):
            create_app(content_export_root=self.export_root / "missing", allow_draft_bundles=True)

    def test_create_app_fails_closed_when_draft_bundle_loading_is_disabled(self):
        with self.assertRaisesRegex(BundleLoadError, "allow_draft_bundles"):
            create_app(content_export_root=self.export_root, allow_draft_bundles=False)

    def test_create_app_fails_closed_when_root_yields_no_topic_bundles(self):
        with self.assertRaisesRegex(BundleLoadError, "topic bundles"):
            create_app(
                content_export_root=self.export_root / "system-design-space",
                allow_draft_bundles=True,
            )

    def test_get_topics_returns_sorted_summary_items_only(self):
        client = TestClient(
            create_app(content_export_root=self.export_root, allow_draft_bundles=True)
        )

        response = client.get("/content/topics")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["topic_slug"] for item in payload],
            ["alpha-topic", "url-shortener", "zeta-topic"],
        )
        self.assertEqual(
            set(payload[0]),
            {
                "topic_slug",
                "display_title",
                "concept_count",
                "pattern_count",
                "scenario_count",
                "review_status",
                "schema_valid",
            },
        )
        self.assertEqual(payload[0]["display_title"], "Кэширование")
        self.assertEqual(payload[0]["schema_valid"], True)
        self.assertNotIn("canonical_content", payload[0])
        self.assertEqual(payload[1]["display_title"], "Design a URL Shortener")
        self.assertEqual(payload[1]["scenario_count"], 1)

    def test_get_topics_uses_display_title_fallback_rule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "export_root"
            source_dir = root / "system-design-space" / "scenario-only"
            source_dir.mkdir(parents=True, exist_ok=True)
            package = {
                "package_id": "topicpkg.scenario-only",
                "topic_slug": "scenario-only",
                "source_document_ids": ["scenario-only"],
                "canonical_content": {
                    "concepts": [],
                    "patterns": [],
                    "scenarios": [
                        {
                            "title": {
                                "value": "Design a News Feed",
                                "provenance": [],
                                "review_required": False,
                            }
                        }
                    ],
                },
                "canonical_support": {"hint_ladders": []},
                "review": {"status": "needs_review", "required_actions": []},
                "validation_summary": {"schema_valid": True, "errors": [], "warnings": []},
            }
            (source_dir / "topic-package.yaml").write_text(
                yaml.safe_dump(package, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            (source_dir / "provenance.json").write_text(
                '{"topic_slug": "scenario-only"}\n',
                encoding="utf-8",
            )
            (source_dir / "validation-report.json").write_text(
                (
                    '{"schema_valid": true, "errors": [], "warnings": [], '
                    '"low_confidence_paths": [], "missing_required_paths": []}\n'
                ),
                encoding="utf-8",
            )

            client = TestClient(create_app(content_export_root=root, allow_draft_bundles=True))
            response = client.get("/content/topics")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[0]["display_title"], "Design a News Feed")

    def test_get_topics_tolerates_nullable_nested_sections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "export_root"
            source_dir = root / "system-design-space" / "nullable-sections"
            source_dir.mkdir(parents=True, exist_ok=True)
            package = {
                "package_id": "topicpkg.nullable-sections",
                "topic_slug": "nullable-sections",
                "source_document_ids": ["nullable-sections"],
                "canonical_content": None,
                "canonical_support": {"hint_ladders": []},
                "review": None,
                "validation_summary": None,
            }
            (source_dir / "topic-package.yaml").write_text(
                yaml.safe_dump(package, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            (source_dir / "provenance.json").write_text(
                '{"topic_slug": "nullable-sections"}\n',
                encoding="utf-8",
            )
            (source_dir / "validation-report.json").write_text(
                (
                    '{"schema_valid": true, "errors": [], "warnings": [], '
                    '"low_confidence_paths": [], "missing_required_paths": []}\n'
                ),
                encoding="utf-8",
            )

            client = TestClient(create_app(content_export_root=root, allow_draft_bundles=True))
            response = client.get("/content/topics")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                [
                    {
                        "topic_slug": "nullable-sections",
                        "display_title": "nullable-sections",
                        "concept_count": 0,
                        "pattern_count": 0,
                        "scenario_count": 0,
                        "review_status": None,
                        "schema_valid": True,
                    }
                ],
            )

    def test_get_topic_returns_projected_detail_without_provenance(self):
        client = TestClient(
            create_app(content_export_root=self.export_root, allow_draft_bundles=True)
        )

        response = client.get("/content/topics/alpha-topic")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["topic_slug"], "alpha-topic")
        self.assertEqual(payload["bundle_source_name"], "system-design-space")
        self.assertEqual(payload["is_draft_bundle"], True)
        self.assertEqual(payload["source_document_ids"], ["alpha-topic"])
        concept = payload["canonical_content"]["concepts"][0]
        self.assertEqual(concept["title"], "Кэширование")
        self.assertEqual(concept["description"], "Кэш снижает нагрузку и латентность.")
        self.assertNotIn("provenance", payload)
        self.assertNotIn("manifest", payload)
        self.assertNotIn("provenance", concept)
        self.assertNotIn("raw_html_path", str(payload))
        self.assertNotIn("normalized_text_path", str(payload))

    def test_get_topic_projects_seeded_url_shortener_scenario_fields(self):
        client = TestClient(
            create_app(content_export_root=self.export_root, allow_draft_bundles=True)
        )

        response = client.get("/content/topics/url-shortener")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["topic_slug"], "url-shortener")
        scenario = payload["canonical_content"]["scenarios"][0]
        self.assertEqual(scenario["id"], "scenario.url-shortener.basic")
        self.assertEqual(scenario["title"], "Design a URL Shortener")
        self.assertIn("read-heavy", scenario["prompt"])
        self.assertEqual(scenario["content_difficulty_baseline"], "standard")
        self.assertEqual(
            scenario["expected_focus_areas"],
            ["id_generation", "storage_choice", "read_scaling", "caching"],
        )
        self.assertEqual(
            scenario["canonical_axes"],
            ["read_write_ratio", "redirect_latency", "collision_avoidance"],
        )
        self.assertEqual(len(scenario["canonical_follow_up_candidates"]), 3)

    def test_get_topic_returns_404_for_unknown_slug(self):
        client = TestClient(
            create_app(content_export_root=self.export_root, allow_draft_bundles=True)
        )

        response = client.get("/content/topics/missing-topic")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
