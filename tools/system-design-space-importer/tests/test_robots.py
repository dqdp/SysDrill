import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from system_design_space_importer.discovery import run_discovery
from system_design_space_importer.fetcher import run_fetch
from system_design_space_importer.paths import RunLayout
from system_design_space_importer.robots import parse_robots_txt


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class FakeHeaders:
    def __init__(self, content_type="text/plain", charset="utf-8"):
        self._content_type = content_type
        self._charset = charset

    def get_content_type(self):
        return self._content_type

    def get_content_charset(self):
        return self._charset


class FakeResponse:
    def __init__(self, body, status=200, content_type="text/plain", charset="utf-8"):
        self._body = body.encode(charset)
        self.status = status
        self.headers = FakeHeaders(content_type=content_type, charset=charset)

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class RobotsPolicyTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "out"
        self.run_id = "robots-run"
        self.layout = RunLayout(out_dir=self.out_dir, run_id=self.run_id)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_robots_txt_extracts_crawl_delay_and_disallow(self):
        robots_text = """
        User-agent: *
        Crawl-delay: 2
        Disallow: /admin/
        Disallow: /private/
        """

        policy = parse_robots_txt(robots_text, user_agent="system-design-space-importer")

        self.assertEqual(policy["crawl_delay_s"], 2.0)
        self.assertEqual(policy["disallow_paths"], ["/admin/", "/private/"])
        self.assertEqual(policy["user_agent"], "system-design-space-importer")

    def test_run_discovery_fetches_robots_policy_for_allowed_http_seed(self):
        with patch(
            "system_design_space_importer.robots.urlopen",
            return_value=FakeResponse(
                """
                User-agent: *
                Crawl-delay: 2
                Disallow: /private/
                """
            ),
        ):
            manifest = run_discovery(
                self.layout,
                seed="https://system-design.space/chapter/event-driven-architecture/",
                profile="chapters_only",
            )

        self.assertEqual(manifest["robots_policy"]["status"], "fetched")
        self.assertEqual(manifest["robots_policy"]["crawl_delay_s"], 2.0)
        self.assertEqual(
            manifest["robots_policy"]["source_url"], "https://system-design.space/robots.txt"
        )
        self.assertEqual(manifest["robots_policy"]["disallow_paths"], ["/private/"])

    def test_fetch_uses_max_of_rate_limit_and_robots_crawl_delay(self):
        self.layout.ensure_base()
        manifest = {
            "run_id": self.run_id,
            "created_at": "2026-03-19T00:00:00+00:00",
            "profile": "chapters_only",
            "seed": "https://system-design.space/chapter/event-driven-architecture/",
            "urls": ["https://system-design.space/chapter/event-driven-architecture/"],
            "fetch_policy": {
                "allowed_hostnames": ["system-design.space", "www.system-design.space"],
                "allow_file_scheme": True,
                "timeout_s": 10,
                "max_retries": 1,
                "rate_limit_ms": 250,
            },
            "robots_policy": {
                "status": "fetched",
                "source_url": "https://system-design.space/robots.txt",
                "user_agent": "system-design-space-importer",
                "crawl_delay_s": 2.0,
                "disallow_paths": [],
            },
        }
        self.layout.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.layout.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with (
            patch(
                "system_design_space_importer.fetcher.urlopen",
                return_value=FakeResponse(
                    """
                <html><body><main><article>
                <h1>Event-Driven Architecture</h1>
                <p>Async event communication with durable consumers.</p>
                </article></main></body></html>
                """,
                    content_type="text/html",
                ),
            ),
            patch("system_design_space_importer.fetcher.time.sleep") as sleep_mock,
        ):
            run_fetch(self.layout)

        sleep_mock.assert_called_once_with(2.0)
        source_document = _load_json(
            self.out_dir
            / "runs"
            / self.run_id
            / "documents"
            / "event-driven-architecture"
            / "source_document.json"
        )
        self.assertEqual(source_document["fetch_metadata"]["effective_rate_limit_ms"], 2000)
        self.assertEqual(source_document["fetch_metadata"]["robots_crawl_delay_s"], 2.0)


if __name__ == "__main__":
    unittest.main()
