import copy
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app
from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.session_runtime import (
    SessionNotFoundError,
    SessionRuntime,
    SessionRuntimeInvalidStateError,
    UnitModeIntentMismatchError,
    UnitNotFoundError,
)


class SessionRuntimeServiceTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.catalog = load_topic_catalog(export_root, allow_draft_bundles=True)
        self.runtime = SessionRuntime(self.catalog)
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"
        self.practice_unit_id = "elu.concept_recall.practice.remediate.concept.alpha-topic"

    def test_manual_start_returns_awaiting_answer_and_emits_events_in_order(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
            source="web",
        )

        self.assertEqual(session["state"], "awaiting_answer")
        self.assertEqual(session["planned_unit_ids"], [self.study_unit_id])
        self.assertEqual(session["current_unit"]["id"], self.study_unit_id)
        events = self.runtime.list_session_events(session["session_id"])
        self.assertEqual(
            [event["event_type"] for event in events],
            ["session_planned", "session_started", "unit_presented"],
        )
        self.assertEqual(events[0]["content_id"], "concept.alpha-topic")
        self.assertTrue(events[0]["event_id"].startswith("event."))
        self.assertEqual(events[0]["mode"], "Study")
        self.assertEqual(events[0]["session_intent"], "LearnNew")
        self.assertEqual(events[0]["source"], "web")
        self.assertIn("occurred_at", events[0])
        self.assertIn("trace_id", events[0])

    def test_get_session_returns_snapshot(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        snapshot = self.runtime.get_session(session["session_id"])

        self.assertEqual(snapshot["session_id"], session["session_id"])
        self.assertEqual(snapshot["current_unit"]["id"], self.study_unit_id)
        event_ids = [
            event["event_id"] for event in self.runtime.list_session_events(session["session_id"])
        ]
        self.assertEqual(
            snapshot["event_ids"],
            event_ids,
        )

    def test_unknown_unit_fails_closed(self):
        with self.assertRaisesRegex(UnitNotFoundError, "unknown unit_id"):
            self.runtime.start_manual_session(
                user_id="user-1",
                mode="Study",
                session_intent="LearnNew",
                unit_id="elu.missing",
            )

    def test_mode_intent_mismatch_fails_closed(self):
        with self.assertRaisesRegex(UnitModeIntentMismatchError, "not available"):
            self.runtime.start_manual_session(
                user_id="user-1",
                mode="Study",
                session_intent="LearnNew",
                unit_id=self.practice_unit_id,
            )

    def test_answer_submission_appends_event_and_builds_evaluation_request(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        events_before = copy.deepcopy(self.runtime.list_session_events(session["session_id"]))

        result = self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Caching reduces latency and load on the database.",
            response_modality="text",
            submission_kind="manual_submit",
            response_latency_ms=42000,
        )

        self.assertEqual(result["session"]["state"], "evaluation_pending")
        self.assertEqual(result["submitted_unit_id"], self.study_unit_id)
        self.assertEqual(
            result["evaluation_request"],
            {
                "session_id": session["session_id"],
                "session_mode": "Study",
                "session_intent": "LearnNew",
                "executable_unit_id": self.study_unit_id,
                "binding_id": "binding.concept_recall.v1",
                "transcript_text": "Caching reduces latency and load on the database.",
                "hint_usage_summary": {
                    "hint_count": 0,
                    "used_prior_hints": False,
                },
                "answer_reveal_flag": False,
                "timing_summary": {
                    "response_latency_ms": 42000,
                },
                "completion_status": "submitted",
                "strictness_profile": "supportive",
            },
        )
        events_after = self.runtime.list_session_events(session["session_id"])
        self.assertEqual(events_after[: len(events_before)], events_before)
        self.assertEqual(events_after[-1]["event_type"], "answer_submitted")
        self.assertEqual(events_after[-1]["payload"]["char_count"], 49)

    def test_repeated_submission_from_invalid_state_fails_closed(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Caching reduces latency and load on the database.",
            response_modality="text",
            submission_kind="manual_submit",
        )

        with self.assertRaisesRegex(SessionRuntimeInvalidStateError, "cannot submit"):
            self.runtime.submit_answer(
                session_id=session["session_id"],
                transcript="Second attempt",
                response_modality="text",
                submission_kind="manual_submit",
            )

    def test_get_unknown_session_fails_closed(self):
        with self.assertRaisesRegex(SessionNotFoundError, "unknown session_id"):
            self.runtime.get_session("session.missing")


class SessionRuntimeApiTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.client = TestClient(
            create_app(content_export_root=export_root, allow_draft_bundles=True)
        )
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"

    def test_manual_start_endpoint_returns_session_snapshot(self):
        response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "user-1",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["state"], "awaiting_answer")
        self.assertEqual(payload["planned_unit_ids"], [self.study_unit_id])
        self.assertEqual(len(payload["event_ids"]), 3)

    def test_get_session_endpoint_returns_snapshot(self):
        start_response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "user-1",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )
        session_id = start_response.json()["session_id"]

        response = self.client.get("/runtime/sessions/{0}".format(session_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["session_id"], session_id)
        self.assertEqual(response.json()["current_unit"]["id"], self.study_unit_id)

    def test_answer_submission_endpoint_returns_evaluation_handoff(self):
        start_response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "user-1",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )
        session_id = start_response.json()["session_id"]

        response = self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json={
                "transcript": "Caching reduces latency and load on the database.",
                "response_modality": "text",
                "submission_kind": "manual_submit",
                "response_latency_ms": 42000,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["session_id"], session_id)
        self.assertEqual(payload["state"], "evaluation_pending")
        self.assertEqual(payload["submitted_unit_id"], self.study_unit_id)
        self.assertEqual(payload["evaluation_request"]["binding_id"], "binding.concept_recall.v1")

    def test_unknown_unit_returns_404(self):
        response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "user-1",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": "elu.missing",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_repeated_submission_returns_409(self):
        start_response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "user-1",
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )
        session_id = start_response.json()["session_id"]
        answer_payload = {
            "transcript": "Caching reduces latency and load on the database.",
            "response_modality": "text",
            "submission_kind": "manual_submit",
        }

        first_response = self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json=answer_payload,
        )
        second_response = self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json=answer_payload,
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
