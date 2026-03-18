import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app


class BackendManualReviewedLoopSmokeTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.client = TestClient(
            create_app(content_export_root=export_root, allow_draft_bundles=True)
        )
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"

    def test_manual_reviewed_loop_reaches_review_presented(self):
        topics_response = self.client.get("/content/topics")
        self.assertEqual(topics_response.status_code, 200)
        self.assertEqual(
            [item["topic_slug"] for item in topics_response.json()],
            ["alpha-topic", "zeta-topic"],
        )

        start_response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "smoke-user",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )
        self.assertEqual(start_response.status_code, 200)
        session_payload = start_response.json()
        self.assertEqual(session_payload["state"], "awaiting_answer")
        session_id = session_payload["session_id"]

        answer_response = self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json={
                "transcript": (
                    "Caching is storing frequently accessed data in a faster layer. "
                    "Use it for read-heavy or latency-sensitive paths. The trade-offs "
                    "are stale data and invalidation complexity."
                ),
                "response_modality": "text",
                "submission_kind": "manual_submit",
                "response_latency_ms": 42000,
            },
        )
        self.assertEqual(answer_response.status_code, 200)
        self.assertEqual(answer_response.json()["state"], "evaluation_pending")

        evaluate_response = self.client.post("/runtime/sessions/{0}/evaluate".format(session_id))
        self.assertEqual(evaluate_response.status_code, 200)
        evaluate_payload = evaluate_response.json()
        self.assertEqual(evaluate_payload["state"], "review_presented")
        self.assertEqual(
            evaluate_payload["evaluation_result"]["binding_id"],
            "binding.concept_recall.v1",
        )
        self.assertIn("weighted_score", evaluate_payload["evaluation_result"])
        self.assertIn("strengths", evaluate_payload["review_report"])

        review_response = self.client.get("/runtime/sessions/{0}/review".format(session_id))
        self.assertEqual(review_response.status_code, 200)
        review_payload = review_response.json()
        self.assertEqual(review_payload["state"], "review_presented")
        self.assertEqual(
            review_payload["evaluation_result"]["evaluation_id"],
            evaluate_payload["evaluation_result"]["evaluation_id"],
        )
        self.assertEqual(
            review_payload["review_report"]["linked_evaluation_ids"],
            [evaluate_payload["evaluation_result"]["evaluation_id"]],
        )


if __name__ == "__main__":
    unittest.main()
