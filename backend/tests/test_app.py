import unittest

from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app


class FastApiAppTest(unittest.TestCase):
    def test_health_endpoint_returns_ok(self):
        client = TestClient(create_app())
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
