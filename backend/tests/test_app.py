import importlib
import os
import unittest

from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app


class FastApiAppTest(unittest.TestCase):
    def test_health_endpoint_returns_ok(self):
        client = TestClient(create_app())
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_module_level_app_uses_environment_configuration(self):
        export_root = (
            os.path.join(os.path.dirname(__file__), "fixtures", "export_root")
        )
        original_values = {
            "SYSDRILL_CONTENT_EXPORT_ROOT": os.environ.get("SYSDRILL_CONTENT_EXPORT_ROOT"),
            "SYSDRILL_ALLOW_DRAFT_BUNDLES": os.environ.get("SYSDRILL_ALLOW_DRAFT_BUNDLES"),
        }
        module = importlib.import_module("sysdrill_backend.app")

        try:
            os.environ["SYSDRILL_CONTENT_EXPORT_ROOT"] = export_root
            os.environ["SYSDRILL_ALLOW_DRAFT_BUNDLES"] = "true"
            module = importlib.reload(module)

            client = TestClient(module.app)
            response = client.get("/content/topics")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                [item["topic_slug"] for item in response.json()],
                ["alpha-topic", "zeta-topic"],
            )
        finally:
            for key, value in original_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(module)


if __name__ == "__main__":
    unittest.main()
