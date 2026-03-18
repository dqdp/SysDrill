import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from system_design_space_importer.discovery import run_discovery
from system_design_space_importer.fetcher import run_fetch
from system_design_space_importer.paths import RunLayout


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class FakeHeaders:
    def __init__(self, content_type="text/html", charset="utf-8"):
        self._content_type = content_type
        self._charset = charset

    def get_content_type(self):
        return self._content_type

    def get_content_charset(self):
        return self._charset


class FakeResponse:
    def __init__(self, body, status=200, content_type="text/html", charset="utf-8"):
        self._body = body.encode(charset)
        self.status = status
        self.headers = FakeHeaders(content_type=content_type, charset=charset)

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FetchPolicyTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name) / "out"
        self.run_id = "policy-run"
        self.layout = RunLayout(out_dir=self.out_dir, run_id=self.run_id)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_discovery_manifest_includes_fetch_policy(self):
        with patch(
            "system_design_space_importer.robots.urlopen",
            return_value=FakeResponse("User-agent: *\n"),
        ):
            manifest = run_discovery(
                self.layout,
                seed="https://system-design.space/chapter/event-driven-architecture/",
                profile="chapters_only",
            )

        self.assertEqual(
            manifest["fetch_policy"]["allowed_hostnames"],
            ["system-design.space", "www.system-design.space"],
        )
        self.assertEqual(manifest["fetch_policy"]["timeout_s"], 10)
        self.assertEqual(manifest["fetch_policy"]["max_retries"], 1)
        self.assertEqual(manifest["fetch_policy"]["rate_limit_ms"], 250)
        self.assertTrue(manifest["fetch_policy"]["allow_file_scheme"])

    def test_fetch_blocks_disallowed_http_host_before_network_call(self):
        self.layout.ensure_base()
        manifest = {
            "run_id": self.run_id,
            "created_at": "2026-03-19T00:00:00+00:00",
            "profile": "chapters_only",
            "seed": "https://system-design.space/",
            "urls": ["https://example.com/chapter/foreign-page/"],
            "fetch_policy": {
                "allowed_hostnames": ["system-design.space", "www.system-design.space"],
                "allow_file_scheme": True,
                "timeout_s": 10,
                "max_retries": 1,
                "rate_limit_ms": 250,
            },
        }
        manifest_path = self.layout.manifest_path
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "disallowed host"):
            run_fetch(self.layout)

    def test_fetch_writes_http_policy_metadata_for_allowed_host(self):
        with patch(
            "system_design_space_importer.robots.urlopen",
            return_value=FakeResponse("User-agent: *\n"),
        ):
            run_discovery(
                self.layout,
                seed="https://system-design.space/chapter/event-driven-architecture/",
                profile="chapters_only",
            )

        with patch(
            "system_design_space_importer.fetcher.urlopen",
            return_value=FakeResponse(
                """
                <html><body><main><article>
                <h1>Event-Driven Architecture</h1>
                <p>Async event communication with durable consumers.</p>
                </article></main></body></html>
                """
            ),
        ):
            documents = run_fetch(self.layout)

        self.assertEqual(len(documents), 1)
        source_document = _load_json(
            self.out_dir
            / "runs"
            / self.run_id
            / "documents"
            / "event-driven-architecture"
            / "source_document.json"
        )
        self.assertEqual(source_document["fetch_mode"], "http_only")
        self.assertEqual(source_document["fetch_metadata"]["timeout_s"], 10)
        self.assertEqual(source_document["fetch_metadata"]["max_retries"], 1)
        self.assertEqual(source_document["fetch_metadata"]["rate_limit_ms"], 250)
        self.assertEqual(source_document["fetch_metadata"]["attempt_count"], 1)

    def test_fetch_retries_http_failures_within_policy_limit(self):
        with patch(
            "system_design_space_importer.robots.urlopen",
            return_value=FakeResponse("User-agent: *\n"),
        ):
            run_discovery(
                self.layout,
                seed="https://system-design.space/chapter/event-driven-architecture/",
                profile="chapters_only",
            )

        responses = [
            RuntimeError("temporary failure"),
            FakeResponse(
                """
                <html><body><main><article>
                <h1>Event-Driven Architecture</h1>
                <p>Async event communication with durable consumers.</p>
                </article></main></body></html>
                """
            ),
        ]

        def fake_urlopen(*args, **kwargs):
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch("system_design_space_importer.fetcher.urlopen", side_effect=fake_urlopen):
            documents = run_fetch(self.layout)

        self.assertEqual(len(documents), 1)
        source_document = _load_json(
            self.out_dir
            / "runs"
            / self.run_id
            / "documents"
            / "event-driven-architecture"
            / "source_document.json"
        )
        self.assertEqual(source_document["fetch_metadata"]["attempt_count"], 2)


if __name__ == "__main__":
    unittest.main()
