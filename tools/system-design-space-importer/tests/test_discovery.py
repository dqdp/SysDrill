import json
import tempfile
import unittest
from pathlib import Path

from system_design_space_importer.discovery import discover_urls, run_discovery
from system_design_space_importer.paths import RunLayout


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.index_fixture = Path(__file__).parent / "fixtures" / "raw_html" / "index.html"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "out"
        self.run_id = "discovery-run"
        self.layout = RunLayout(out_dir=self.out_dir, run_id=self.run_id)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_discover_urls_extracts_allowed_chapter_links_from_index_fixture(self):
        urls = discover_urls(
            seed=self.index_fixture.resolve().as_uri(),
            profile="chapters_only",
        )

        self.assertEqual(
            urls,
            [
                "https://system-design.space/chapter/event-driven-architecture/",
                "https://system-design.space/chapter/caching-strategies/",
                "https://system-design.space/chapter/rate-limiter/",
                "https://system-design.space/chapter/notification-system/",
            ],
        )

    def test_discover_urls_applies_max_pages_after_deduplication(self):
        urls = discover_urls(
            seed=self.index_fixture.resolve().as_uri(),
            profile="chapters_only",
            max_pages=2,
        )

        self.assertEqual(
            urls,
            [
                "https://system-design.space/chapter/event-driven-architecture/",
                "https://system-design.space/chapter/caching-strategies/",
            ],
        )

    def test_run_discovery_persists_discovery_policy_in_manifest(self):
        manifest = run_discovery(
            self.layout,
            seed=self.index_fixture.resolve().as_uri(),
            profile="chapters_only",
        )

        self.assertEqual(manifest["discovery_policy"]["allowed_path_prefixes"], ["/chapter/"])
        self.assertTrue(manifest["discovery_policy"]["deduplicate_urls"])

        persisted = _load_json(self.layout.manifest_path)
        self.assertEqual(persisted["discovery_policy"]["allowed_path_prefixes"], ["/chapter/"])

    def test_run_discovery_matches_manifest_snapshot_for_local_index_fixture(self):
        manifest = run_discovery(
            self.layout,
            seed=self.index_fixture.resolve().as_uri(),
            profile="chapters_only",
        )

        normalized_manifest = dict(manifest)
        normalized_manifest["created_at"] = "<normalized>"
        normalized_manifest["run_id"] = "<normalized>"
        normalized_manifest["seed"] = "<normalized>"

        expected_snapshot = _load_json(
            Path(__file__).parent / "fixtures" / "expected" / "discovery-manifest.snapshot.json"
        )
        self.assertEqual(normalized_manifest, expected_snapshot)

    def test_discover_urls_keeps_single_allowed_seed_chapter(self):
        seed = "https://system-design.space/chapter/event-driven-architecture/"

        urls = discover_urls(seed=seed, profile="chapters_only")

        self.assertEqual(urls, [seed])


if __name__ == "__main__":
    unittest.main()
