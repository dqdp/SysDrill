import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app
from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.learner_summary import build_content_title_map, build_learner_summary


class LearnerSummaryRuleTest(unittest.TestCase):
    def test_empty_profile_returns_neutral_summary(self):
        summary = build_learner_summary(
            {
                "user_id": "user-1",
                "concept_state": {},
                "subskill_state": {},
                "trajectory_state": {
                    "recent_fatigue_signal": 0.0,
                    "recent_abandonment_signal": 0.0,
                    "mock_readiness_estimate": 0.0,
                    "mock_readiness_confidence": 0.0,
                    "last_active_at": None,
                },
                "last_updated_at": None,
            }
        )

        self.assertEqual(summary["weak_areas"], [])
        self.assertEqual(summary["review_due"], [])
        self.assertEqual(
            summary["readiness_summary"]["category"],
            "insufficient_evidence",
        )
        self.assertEqual(
            summary["evidence_posture"]["category"],
            "insufficient_evidence",
        )

    def test_summary_surfaces_confirmed_weakness_and_review_due_consistently(self):
        summary = build_learner_summary(
            {
                "user_id": "user-1",
                "concept_state": {
                    "concept.alpha-topic": {
                        "proficiency_estimate": 0.32,
                        "confidence": 0.61,
                        "review_due_risk": 0.82,
                        "hint_dependency_signal": 0.28,
                        "last_evidence_at": "2026-03-20T10:00:00Z",
                    },
                },
                "subskill_state": {
                    "tradeoff_reasoning": {
                        "proficiency_estimate": 0.35,
                        "confidence": 0.58,
                        "last_evidence_at": "2026-03-20T10:00:00Z",
                    },
                },
                "trajectory_state": {
                    "recent_fatigue_signal": 0.0,
                    "recent_abandonment_signal": 0.0,
                    "mock_readiness_estimate": 0.18,
                    "mock_readiness_confidence": 0.14,
                    "last_active_at": "2026-03-20T10:00:00Z",
                },
                "last_updated_at": "2026-03-20T10:00:00Z",
            },
            content_titles={"concept.alpha-topic": "Кэширование"},
        )

        self.assertEqual(summary["weak_areas"][0]["target_id"], "concept.alpha-topic")
        self.assertEqual(summary["weak_areas"][0]["posture"], "weak")
        self.assertEqual(summary["review_due"][0]["target_id"], "concept.alpha-topic")
        self.assertEqual(
            summary["evidence_posture"]["category"],
            "conservative_summary",
        )

    def test_readiness_summary_stays_conservative_under_abandonment(self):
        summary = build_learner_summary(
            {
                "user_id": "user-1",
                "concept_state": {},
                "subskill_state": {},
                "trajectory_state": {
                    "recent_fatigue_signal": 0.62,
                    "recent_abandonment_signal": 0.45,
                    "mock_readiness_estimate": 0.4,
                    "mock_readiness_confidence": 0.32,
                    "last_active_at": "2026-03-20T10:00:00Z",
                },
                "last_updated_at": "2026-03-20T10:00:00Z",
            }
        )

        self.assertEqual(summary["readiness_summary"]["category"], "stabilize_first")

    def test_mock_only_evidence_keeps_readiness_non_empty_without_scenario_weak_areas(self):
        summary = build_learner_summary(
            {
                "user_id": "user-1",
                "concept_state": {},
                "subskill_state": {
                    "tradeoff_reasoning": {
                        "proficiency_estimate": 0.74,
                        "confidence": 0.31,
                        "last_evidence_at": "2026-03-21T10:00:00Z",
                    },
                    "communication_clarity": {
                        "proficiency_estimate": 0.71,
                        "confidence": 0.29,
                        "last_evidence_at": "2026-03-21T10:00:00Z",
                    },
                },
                "trajectory_state": {
                    "recent_fatigue_signal": 0.0,
                    "recent_abandonment_signal": 0.0,
                    "mock_readiness_estimate": 0.24,
                    "mock_readiness_confidence": 0.2,
                    "last_active_at": "2026-03-21T10:00:00Z",
                },
                "last_updated_at": "2026-03-21T10:00:00Z",
            }
        )

        self.assertEqual(summary["weak_areas"], [])
        self.assertEqual(summary["review_due"], [])
        self.assertEqual(summary["readiness_summary"]["category"], "not_ready_yet")

    def test_content_title_map_includes_seeded_url_shortener_concepts(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        catalog = load_topic_catalog(export_root, allow_draft_bundles=True)

        title_map = build_content_title_map(catalog)

        self.assertEqual(
            title_map["concept.url-shortener.storage-choice"],
            "Storage choice for short URL mappings",
        )
        self.assertEqual(
            title_map["concept.url-shortener.id-generation"],
            "ID generation for short URLs",
        )

    def test_summary_surfaces_bound_url_shortener_concepts_not_raw_scenario_ids(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        catalog = load_topic_catalog(export_root, allow_draft_bundles=True)
        title_map = build_content_title_map(catalog)

        summary = build_learner_summary(
            {
                "user_id": "user-1",
                "concept_state": {
                    "concept.url-shortener.storage-choice": {
                        "proficiency_estimate": 0.33,
                        "confidence": 0.62,
                        "review_due_risk": 0.81,
                        "hint_dependency_signal": 0.15,
                        "last_evidence_at": "2026-03-21T10:00:00Z",
                    }
                },
                "subskill_state": {
                    "tradeoff_reasoning": {
                        "proficiency_estimate": 0.41,
                        "confidence": 0.58,
                        "last_evidence_at": "2026-03-21T10:00:00Z",
                    },
                },
                "trajectory_state": {
                    "recent_fatigue_signal": 0.0,
                    "recent_abandonment_signal": 0.0,
                    "mock_readiness_estimate": 0.22,
                    "mock_readiness_confidence": 0.2,
                    "last_active_at": "2026-03-21T10:00:00Z",
                },
                "last_updated_at": "2026-03-21T10:00:00Z",
            },
            content_titles=title_map,
        )

        self.assertEqual(
            summary["weak_areas"][0]["title"],
            "Storage choice for short URL mappings",
        )
        self.assertEqual(
            summary["review_due"][0]["title"],
            "Storage choice for short URL mappings",
        )
        self.assertNotIn("scenario.url-shortener.basic", str(summary))

    def test_mock_weak_concept_can_surface_without_becoming_review_due(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        catalog = load_topic_catalog(export_root, allow_draft_bundles=True)
        title_map = build_content_title_map(catalog)

        summary = build_learner_summary(
            {
                "user_id": "user-1",
                "concept_state": {
                    "concept.url-shortener.storage-choice": {
                        "proficiency_estimate": 0.4,
                        "confidence": 0.38,
                        "review_due_risk": 0.42,
                        "hint_dependency_signal": 0.12,
                        "last_evidence_at": "2026-03-21T10:00:00Z",
                    }
                },
                "subskill_state": {},
                "trajectory_state": {
                    "recent_fatigue_signal": 0.0,
                    "recent_abandonment_signal": 0.0,
                    "mock_readiness_estimate": 0.18,
                    "mock_readiness_confidence": 0.16,
                    "last_active_at": "2026-03-21T10:00:00Z",
                },
                "last_updated_at": "2026-03-21T10:00:00Z",
            },
            content_titles=title_map,
        )

        self.assertEqual(
            summary["weak_areas"][0]["target_id"],
            "concept.url-shortener.storage-choice",
        )
        self.assertEqual(summary["review_due"], [])


class LearnerSummaryApiTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.client = TestClient(
            create_app(content_export_root=export_root, allow_draft_bundles=True)
        )
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"

    def test_learner_summary_endpoint_returns_summary_shaped_payload(self):
        start_response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "demo-user",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )
        session_id = start_response.json()["session_id"]
        self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json={
                "transcript": "Caching is keeping data somewhere faster.",
                "response_modality": "text",
                "submission_kind": "manual_submit",
            },
        )
        self.client.post("/runtime/sessions/{0}/evaluate".format(session_id))

        response = self.client.get("/learner/summary", params={"user_id": "demo-user"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["user_id"], "demo-user")
        self.assertIn("weak_areas", payload)
        self.assertIn("review_due", payload)
        self.assertIn("readiness_summary", payload)
        self.assertIn("evidence_posture", payload)


if __name__ == "__main__":
    unittest.main()
