import copy
import threading
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from sysdrill_backend.app import create_app
from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.session_runtime import (
    SessionNotFoundError,
    SessionRuntime,
    SessionRuntimeError,
    SessionRuntimeInvalidStateError,
    UnitModeIntentMismatchError,
    UnitNotFoundError,
)


class CoordinatedStateReadSession(dict):
    def __init__(
        self,
        payload: dict,
        watched_state: str,
        first_read_event: threading.Event,
        second_read_event: threading.Event,
        release_event: threading.Event,
    ):
        super().__init__(payload)
        self._watched_state = watched_state
        self._first_read_event = first_read_event
        self._second_read_event = second_read_event
        self._release_event = release_event
        self._read_count = 0
        self._coordination_lock = threading.Lock()

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if key == "state" and value == self._watched_state:
            with self._coordination_lock:
                self._read_count += 1
                read_count = self._read_count
                if read_count == 1:
                    self._first_read_event.set()
                elif read_count == 2:
                    self._second_read_event.set()
            if read_count <= 2:
                self._release_event.wait(timeout=1)
        return value


class SessionRuntimeServiceTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.catalog = load_topic_catalog(export_root, allow_draft_bundles=True)
        self.runtime = SessionRuntime(self.catalog)
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"
        self.practice_unit_id = "elu.concept_recall.practice.remediate.concept.alpha-topic"
        self.mock_unit_id = (
            "elu.scenario_readiness_check.mock_interview.readiness_check."
            "scenario.url-shortener.basic"
        )

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
                "unit_family": "concept_recall",
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

    def test_evaluate_pending_session_attaches_evaluation_and_review_events(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching is storing frequently accessed data in a faster layer. "
                "Use it for read-heavy or latency-sensitive paths. The trade-offs "
                "are stale data and invalidation complexity."
            ),
            response_modality="text",
            submission_kind="manual_submit",
            response_latency_ms=42000,
        )

        result = self.runtime.evaluate_pending_session(session["session_id"])
        events = self.runtime.list_session_events(session["session_id"])

        self.assertEqual(result["session"]["state"], "review_presented")
        self.assertEqual(events[-2]["event_type"], "evaluation_attached")
        self.assertEqual(events[-1]["event_type"], "review_presented")
        self.assertEqual(
            result["evaluation_result"]["binding_id"],
            "binding.concept_recall.v1",
        )
        self.assertEqual(
            result["review_report"]["session_id"],
            session["session_id"],
        )
        snapshot = self.runtime.get_session(session["session_id"])
        self.assertEqual(snapshot["state"], "review_presented")
        self.assertIn("last_evaluation_result", snapshot)
        self.assertIn("last_review_report", snapshot)

    def test_complete_session_transitions_reviewed_session_and_preserves_review_access(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching is storing frequently accessed data in a faster layer. "
                "Use it for read-heavy paths. The trade-offs are stale data "
                "and invalidation complexity."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        completed = self.runtime.complete_session(session["session_id"])
        events = self.runtime.list_session_events(session["session_id"])
        review = self.runtime.get_review(session["session_id"])

        self.assertEqual(completed["state"], "completed")
        self.assertEqual(events[-1]["event_type"], "session_completed")
        self.assertEqual(
            events[-1]["payload"]["completed_from_state"],
            "review_presented",
        )
        self.assertEqual(review["session"]["state"], "completed")

    def test_complete_session_fails_closed_outside_review_presented(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        with self.assertRaisesRegex(SessionRuntimeInvalidStateError, "cannot complete"):
            self.runtime.complete_session(session["session_id"])

    def test_abandon_session_marks_in_flight_session_and_emits_event(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        abandoned = self.runtime.abandon_session(
            session["session_id"],
            abandon_reason="explicit_exit",
        )
        events = self.runtime.list_session_events(session["session_id"])

        self.assertEqual(abandoned["state"], "abandoned")
        self.assertEqual(events[-1]["event_type"], "session_abandoned")
        self.assertEqual(events[-1]["payload"]["abandon_reason"], "explicit_exit")
        self.assertEqual(events[-1]["payload"]["abandoned_from_state"], "awaiting_answer")

    def test_abandon_session_rejects_reviewed_session(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching is storing frequently accessed data in a faster layer. "
                "Use it for read-heavy paths. The trade-offs are stale data "
                "and invalidation complexity."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        with self.assertRaisesRegex(SessionRuntimeInvalidStateError, "cannot abandon"):
            self.runtime.abandon_session(session["session_id"])

    def test_request_hint_is_repeatable_and_flows_into_evaluation_request(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        first_hint = self.runtime.request_hint(
            session["session_id"],
            hint_level=1,
            reason="need_more_guidance",
        )
        second_hint = self.runtime.request_hint(
            session["session_id"],
            hint_level=2,
            reason="still_stuck",
        )
        submit_result = self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Caching reduces latency and load on the database.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        events = self.runtime.list_session_events(session["session_id"])

        self.assertEqual(first_hint["state"], "awaiting_answer")
        self.assertEqual(second_hint["hint_count_for_unit"], 2)
        self.assertEqual(
            [event["event_type"] for event in events].count("hint_requested"),
            2,
        )
        self.assertEqual(
            submit_result["evaluation_request"]["hint_usage_summary"],
            {
                "hint_count": 2,
                "used_prior_hints": True,
            },
        )

    def test_answer_reveal_sets_support_flag_for_later_evaluation(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        reveal_result = self.runtime.reveal_answer(
            session["session_id"],
            reveal_kind="canonical_answer",
        )
        submit_result = self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Caching reduces latency and load on the database.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        events = self.runtime.list_session_events(session["session_id"])

        self.assertEqual(reveal_result["state"], "awaiting_answer")
        self.assertEqual(events[-2]["event_type"], "answer_revealed")
        self.assertTrue(submit_result["evaluation_request"]["answer_reveal_flag"])

    def test_answer_reveal_rejects_units_that_do_not_allow_it(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Practice",
            session_intent="Remediate",
            unit_id=self.practice_unit_id,
        )

        with self.assertRaisesRegex(SessionRuntimeError, "answer reveal"):
            self.runtime.reveal_answer(
                session["session_id"],
                reveal_kind="canonical_answer",
            )

    def test_evaluate_pending_session_fails_closed_from_wrong_state(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        with self.assertRaisesRegex(SessionRuntimeInvalidStateError, "evaluation"):
            self.runtime.evaluate_pending_session(session["session_id"])

    def test_submission_kind_mismatch_fails_closed_without_appending_event(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        events_before = copy.deepcopy(self.runtime.list_session_events(session["session_id"]))

        with self.assertRaisesRegex(SessionRuntimeError, "submission_kind"):
            self.runtime.submit_answer(
                session_id=session["session_id"],
                transcript="Caching reduces latency and load on the database.",
                response_modality="text",
                submission_kind="auto_submit",
            )

        self.assertEqual(
            self.runtime.get_session(session["session_id"])["state"],
            "awaiting_answer",
        )
        self.assertEqual(
            self.runtime.list_session_events(session["session_id"]),
            events_before,
        )

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

    def test_list_manual_launch_options_returns_stable_runtime_facing_items(self):
        launch_options = self.runtime.list_manual_launch_options(
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(
            launch_options,
            [
                {
                    "unit_id": "elu.concept_recall.study.learn_new.concept.alpha-topic",
                    "content_id": "concept.alpha-topic",
                    "topic_slug": "alpha-topic",
                    "display_title": "Кэширование",
                    "visible_prompt": (
                        "Explain the concept 'Кэширование'. Cover what it is, "
                        "when to use it, and the main trade-offs."
                    ),
                    "effective_difficulty": "introductory",
                }
            ],
        )

    def test_list_manual_launch_options_returns_richer_practice_prompt_without_shape_change(self):
        launch_options = self.runtime.list_manual_launch_options(
            mode="Practice",
            session_intent="Remediate",
        )

        self.assertEqual(
            launch_options,
            [
                {
                    "unit_id": "elu.concept_recall.practice.remediate.concept.alpha-topic",
                    "content_id": "concept.alpha-topic",
                    "topic_slug": "alpha-topic",
                    "display_title": "Кэширование",
                    "visible_prompt": (
                        "You're advising a teammate on whether to use 'Кэширование' in a "
                        "real system discussion. Context: Кэш снижает нагрузку и "
                        "латентность. Why it matters: Снижает нагрузку на базу данных. "
                        "Explain what it is, when you would use it, and the main "
                        "trade-offs you would call out."
                    ),
                    "effective_difficulty": "targeted",
                }
            ],
        )

    def test_list_manual_launch_options_returns_seeded_mock_readiness_item(self):
        launch_options = self.runtime.list_manual_launch_options(
            mode="MockInterview",
            session_intent="ReadinessCheck",
        )

        self.assertEqual(
            launch_options,
            [
                {
                    "unit_id": self.mock_unit_id,
                    "content_id": "scenario.url-shortener.basic",
                    "topic_slug": "url-shortener",
                    "display_title": "Design a URL Shortener",
                    "visible_prompt": (
                        "Design a URL Shortener for a read-heavy product with high "
                        "availability requirements."
                    ),
                    "effective_difficulty": "standard",
                }
            ],
        )

    def test_list_manual_launch_options_returns_empty_list_for_supported_combo_without_units(self):
        empty_catalog = copy.deepcopy(self.catalog)
        empty_catalog["alpha-topic"]["topic_package"]["learning_design_drafts"][
            "candidate_card_types"
        ] = []
        runtime = SessionRuntime(empty_catalog)

        launch_options = runtime.list_manual_launch_options(
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(launch_options, [])

    def test_list_user_reviewed_outcomes_orders_by_review_timestamp(self):
        first_session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        second_session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        self.runtime.submit_answer(
            session_id=second_session["session_id"],
            transcript=(
                "Caching is storing frequently accessed data in a faster layer. "
                "Use it for read-heavy paths. The trade-offs are stale data "
                "and invalidation complexity."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(second_session["session_id"])
        self.runtime.submit_answer(
            session_id=first_session["session_id"],
            transcript="Caching is keeping data somewhere faster.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(first_session["session_id"])

        outcomes = self.runtime.list_user_reviewed_outcomes("user-1")

        self.assertEqual(
            [outcome["session_id"] for outcome in outcomes],
            [second_session["session_id"], first_session["session_id"]],
        )

    def test_list_manual_launch_options_rejects_unsupported_mode_intent_combination(self):
        with self.assertRaisesRegex(UnitModeIntentMismatchError, "unsupported runtime"):
            self.runtime.list_manual_launch_options(
                mode="Practice",
                session_intent="LearnNew",
            )

    def test_start_from_recommendation_resolves_action_and_emits_acceptance_event(self):
        session = self.runtime.start_session_from_recommendation(
            user_id="user-1",
            decision_id="rec.0001",
            action={
                "mode": "Study",
                "session_intent": "LearnNew",
                "target_type": "concept",
                "target_id": "concept.alpha-topic",
                "difficulty_profile": "introductory",
                "strictness_profile": "supportive",
                "session_size": "single_unit",
                "delivery_profile": "text_first",
                "rationale": "Bootstrap recommendation.",
            },
            source="web",
        )

        self.assertEqual(session["state"], "awaiting_answer")
        self.assertEqual(session["current_unit"]["id"], self.study_unit_id)
        self.assertEqual(session["recommendation_decision_id"], "rec.0001")
        events = self.runtime.list_session_events(session["session_id"])
        self.assertEqual(
            [event["event_type"] for event in events],
            [
                "recommendation_accepted",
                "session_planned",
                "session_started",
                "unit_presented",
            ],
        )
        self.assertEqual(events[0]["payload"]["decision_id"], "rec.0001")
        self.assertEqual(events[0]["payload"]["target_id"], "concept.alpha-topic")

    def test_start_from_recommendation_rejects_illegal_action_profiles(self):
        with self.assertRaisesRegex(SessionRuntimeError, "difficulty_profile"):
            self.runtime.start_session_from_recommendation(
                user_id="user-1",
                decision_id="rec.0001",
                action={
                    "mode": "Study",
                    "session_intent": "LearnNew",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "targeted",
                    "strictness_profile": "supportive",
                    "session_size": "single_unit",
                    "delivery_profile": "text_first",
                    "rationale": "Bootstrap recommendation.",
                },
            )

    def test_recommendation_backed_evaluation_emits_completion_event(self):
        session = self.runtime.start_session_from_recommendation(
            user_id="user-1",
            decision_id="rec.0001",
            action={
                "mode": "Study",
                "session_intent": "LearnNew",
                "target_type": "concept",
                "target_id": "concept.alpha-topic",
                "difficulty_profile": "introductory",
                "strictness_profile": "supportive",
                "session_size": "single_unit",
                "delivery_profile": "text_first",
                "rationale": "Bootstrap recommendation.",
            },
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching is storing frequently accessed data in a faster layer. "
                "Use it for read-heavy paths. The trade-offs are stale data "
                "and invalidation complexity."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )

        result = self.runtime.evaluate_pending_session(session["session_id"])
        events = self.runtime.list_session_events(session["session_id"])

        self.assertEqual(result["session"]["state"], "review_presented")
        self.assertEqual(events[-1]["event_type"], "review_presented")

        completed = self.runtime.complete_session(session["session_id"])
        events = self.runtime.list_session_events(session["session_id"])

        self.assertEqual(completed["state"], "completed")
        self.assertEqual(events[-2]["event_type"], "session_completed")
        self.assertEqual(events[-1]["event_type"], "recommendation_completed")
        self.assertEqual(events[-1]["payload"]["decision_id"], "rec.0001")

    def test_practice_session_submission_and_evaluation_preserve_concept_recall_contract(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Practice",
            session_intent="Remediate",
            unit_id=self.practice_unit_id,
        )

        submit_result = self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching stores frequently accessed data in a faster layer. Use it on "
                "read-heavy or latency-sensitive paths. The trade-offs are stale data, "
                "invalidation complexity, and extra memory cost."
            ),
            response_modality="text",
            submission_kind="manual_submit",
            response_latency_ms=31000,
        )

        self.assertEqual(
            submit_result["evaluation_request"]["binding_id"],
            "binding.concept_recall.v1",
        )
        self.assertEqual(
            submit_result["evaluation_request"]["unit_family"],
            "concept_recall",
        )

        evaluation_result = self.runtime.evaluate_pending_session(session["session_id"])

        self.assertEqual(evaluation_result["session"]["state"], "review_presented")
        self.assertEqual(
            evaluation_result["evaluation_result"]["binding_id"],
            "binding.concept_recall.v1",
        )

    def test_concurrent_submission_yields_single_stable_answer_boundary(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        first_read_event = threading.Event()
        second_read_event = threading.Event()
        release_event = threading.Event()
        coordinated_session = CoordinatedStateReadSession(
            self.runtime._sessions[session["session_id"]],
            watched_state="awaiting_answer",
            first_read_event=first_read_event,
            second_read_event=second_read_event,
            release_event=release_event,
        )
        self.runtime._sessions[session["session_id"]] = coordinated_session
        successes = []
        failures = []

        def worker(transcript: str) -> None:
            try:
                result = self.runtime.submit_answer(
                    session_id=session["session_id"],
                    transcript=transcript,
                    response_modality="text",
                    submission_kind="manual_submit",
                )
                successes.append(result)
            except Exception as exc:  # pragma: no cover - exercised by assertion below
                failures.append(exc)

        first_thread = threading.Thread(target=worker, args=("First attempt",))
        second_thread = threading.Thread(target=worker, args=("Second attempt",))

        first_thread.start()
        self.assertTrue(first_read_event.wait(timeout=1))
        second_thread.start()
        second_read_event.wait(timeout=0.2)
        release_event.set()
        first_thread.join(timeout=1)
        second_thread.join(timeout=1)

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], SessionRuntimeInvalidStateError)
        events = self.runtime.list_session_events(session["session_id"])
        self.assertEqual(
            [event["event_type"] for event in events].count("answer_submitted"),
            1,
        )
        self.assertEqual(
            self.runtime.get_session(session["session_id"])["state"],
            "evaluation_pending",
        )

    def test_concurrent_evaluation_yields_single_reviewed_outcome(self):
        session = self.runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching is storing frequently accessed data in a faster layer. "
                "Use it for read-heavy paths. The trade-offs are stale data "
                "and invalidation complexity."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        first_read_event = threading.Event()
        second_read_event = threading.Event()
        release_event = threading.Event()
        coordinated_session = CoordinatedStateReadSession(
            self.runtime._sessions[session["session_id"]],
            watched_state="evaluation_pending",
            first_read_event=first_read_event,
            second_read_event=second_read_event,
            release_event=release_event,
        )
        self.runtime._sessions[session["session_id"]] = coordinated_session
        successes = []
        failures = []

        def worker() -> None:
            try:
                result = self.runtime.evaluate_pending_session(session["session_id"])
                successes.append(result)
            except Exception as exc:  # pragma: no cover - exercised by assertion below
                failures.append(exc)

        first_thread = threading.Thread(target=worker)
        second_thread = threading.Thread(target=worker)

        first_thread.start()
        self.assertTrue(first_read_event.wait(timeout=1))
        second_thread.start()
        second_read_event.wait(timeout=0.2)
        release_event.set()
        first_thread.join(timeout=1)
        second_thread.join(timeout=1)

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], SessionRuntimeInvalidStateError)
        events = self.runtime.list_session_events(session["session_id"])
        self.assertEqual(
            [event["event_type"] for event in events].count("evaluation_attached"),
            1,
        )
        self.assertEqual(
            [event["event_type"] for event in events].count("review_presented"),
            1,
        )
        self.assertEqual(
            self.runtime.get_session(session["session_id"])["state"],
            "review_presented",
        )


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

    def test_manual_launch_options_endpoint_returns_supported_items(self):
        response = self.client.get(
            "/runtime/manual-launch-options",
            params={
                "mode": "Study",
                "session_intent": "LearnNew",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "mode": "Study",
                "session_intent": "LearnNew",
                "items": [
                    {
                        "unit_id": "elu.concept_recall.study.learn_new.concept.alpha-topic",
                        "content_id": "concept.alpha-topic",
                        "topic_slug": "alpha-topic",
                        "display_title": "Кэширование",
                        "visible_prompt": (
                            "Explain the concept 'Кэширование'. Cover what it is, "
                            "when to use it, and the main trade-offs."
                        ),
                        "effective_difficulty": "introductory",
                    }
                ],
            },
        )

    def test_manual_launch_options_endpoint_returns_richer_practice_prompt(self):
        response = self.client.get(
            "/runtime/manual-launch-options",
            params={
                "mode": "Practice",
                "session_intent": "Remediate",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "mode": "Practice",
                "session_intent": "Remediate",
                "items": [
                    {
                        "unit_id": "elu.concept_recall.practice.remediate.concept.alpha-topic",
                        "content_id": "concept.alpha-topic",
                        "topic_slug": "alpha-topic",
                        "display_title": "Кэширование",
                        "visible_prompt": (
                            "You're advising a teammate on whether to use "
                            "'Кэширование' in a real system discussion. Context: "
                            "Кэш снижает нагрузку и латентность. Why it matters: "
                            "Снижает нагрузку на базу данных. Explain what it is, "
                            "when you would use it, and the main trade-offs you "
                            "would call out."
                        ),
                        "effective_difficulty": "targeted",
                    }
                ],
            },
        )

    def test_manual_launch_options_endpoint_returns_400_for_unsupported_mode_intent(self):
        response = self.client.get(
            "/runtime/manual-launch-options",
            params={
                "mode": "Practice",
                "session_intent": "LearnNew",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("unsupported runtime", response.json()["detail"])

    def test_manual_launch_options_endpoint_requires_query_params(self):
        response = self.client.get("/runtime/manual-launch-options")

        self.assertEqual(response.status_code, 422)

    def test_recommendations_next_endpoint_returns_structured_decision(self):
        response = self.client.post(
            "/recommendations/next",
            json={"user_id": "demo-user"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["policy_version"], "bootstrap.recommendation.v1")
        self.assertEqual(payload["decision_mode"], "rule_based")
        self.assertEqual(payload["chosen_action"]["mode"], "Study")
        self.assertEqual(payload["chosen_action"]["session_intent"], "LearnNew")
        self.assertEqual(payload["chosen_action"]["target_id"], "concept.alpha-topic")
        self.assertNotIn("unit_id", payload["chosen_action"])

    def test_start_from_recommendation_endpoint_returns_session_snapshot(self):
        recommendation_response = self.client.post(
            "/recommendations/next",
            json={"user_id": "demo-user"},
        )
        decision = recommendation_response.json()

        response = self.client.post(
            "/runtime/sessions/start-from-recommendation",
            json={
                "user_id": "demo-user",
                "decision_id": decision["decision_id"],
                "action": decision["chosen_action"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["state"], "awaiting_answer")
        self.assertEqual(payload["current_unit"]["id"], self.study_unit_id)
        self.assertEqual(payload["recommendation_decision_id"], decision["decision_id"])

    def test_start_from_recommendation_endpoint_returns_404_for_unknown_decision(self):
        response = self.client.post(
            "/runtime/sessions/start-from-recommendation",
            json={
                "user_id": "demo-user",
                "decision_id": "rec.missing",
                "action": {
                    "mode": "Study",
                    "session_intent": "LearnNew",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "introductory",
                    "strictness_profile": "supportive",
                    "session_size": "single_unit",
                    "delivery_profile": "text_first",
                    "rationale": "Bootstrap recommendation.",
                },
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_start_from_recommendation_endpoint_returns_400_for_action_mismatch(self):
        recommendation_response = self.client.post(
            "/recommendations/next",
            json={"user_id": "demo-user"},
        )
        decision = recommendation_response.json()
        mismatched_action = copy.deepcopy(decision["chosen_action"])
        mismatched_action["session_intent"] = "Reinforce"

        response = self.client.post(
            "/runtime/sessions/start-from-recommendation",
            json={
                "user_id": "demo-user",
                "decision_id": decision["decision_id"],
                "action": mismatched_action,
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_start_from_recommendation_endpoint_returns_409_for_reused_decision(self):
        recommendation_response = self.client.post(
            "/recommendations/next",
            json={"user_id": "demo-user"},
        )
        decision = recommendation_response.json()

        first_response = self.client.post(
            "/runtime/sessions/start-from-recommendation",
            json={
                "user_id": "demo-user",
                "decision_id": decision["decision_id"],
                "action": decision["chosen_action"],
            },
        )
        second_response = self.client.post(
            "/runtime/sessions/start-from-recommendation",
            json={
                "user_id": "demo-user",
                "decision_id": decision["decision_id"],
                "action": decision["chosen_action"],
            },
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)

    def test_recommendations_next_endpoint_returns_503_without_runtime_content(self):
        client = TestClient(create_app())

        response = client.post(
            "/recommendations/next",
            json={"user_id": "demo-user"},
        )

        self.assertEqual(response.status_code, 503)

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

    def test_manual_start_endpoint_rejects_missing_required_fields_with_422(self):
        response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "mode": "Study",
                "session_intent": "LearnNew",
                "unit_id": self.study_unit_id,
            },
        )

        self.assertEqual(response.status_code, 422)

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
        self.assertEqual(payload["evaluation_request"]["unit_family"], "concept_recall")

    def test_answer_submission_endpoint_rejects_invalid_payload_with_422(self):
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
                "submission_kind": 42,
            },
        )

        self.assertEqual(response.status_code, 422)

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

    def test_evaluate_endpoint_returns_reviewed_outcome(self):
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
        self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json={
                "transcript": (
                    "Caching is storing frequently accessed data in a faster layer. "
                    "Use it for read-heavy paths. The trade-offs are stale data "
                    "and invalidation complexity."
                ),
                "response_modality": "text",
                "submission_kind": "manual_submit",
            },
        )

        response = self.client.post("/runtime/sessions/{0}/evaluate".format(session_id))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["session_id"], session_id)
        self.assertEqual(payload["state"], "review_presented")
        self.assertIn("evaluation_result", payload)
        self.assertIn("review_report", payload)

    def test_get_review_endpoint_returns_review_after_evaluation(self):
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
        self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json={
                "transcript": (
                    "Caching is storing frequently accessed data in a faster layer. "
                    "Use it for read-heavy paths. The trade-offs are stale data "
                    "and invalidation complexity."
                ),
                "response_modality": "text",
                "submission_kind": "manual_submit",
            },
        )
        self.client.post("/runtime/sessions/{0}/evaluate".format(session_id))

        response = self.client.get("/runtime/sessions/{0}/review".format(session_id))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["session_id"], session_id)
        self.assertIn("evaluation_result", payload)
        self.assertIn("review_report", payload)

    def test_complete_endpoint_transitions_reviewed_session(self):
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
        self.client.post(
            "/runtime/sessions/{0}/answer".format(session_id),
            json={
                "transcript": (
                    "Caching is storing frequently accessed data in a faster layer. "
                    "Use it for read-heavy paths. The trade-offs are stale data "
                    "and invalidation complexity."
                ),
                "response_modality": "text",
                "submission_kind": "manual_submit",
            },
        )
        self.client.post("/runtime/sessions/{0}/evaluate".format(session_id))

        response = self.client.post("/runtime/sessions/{0}/complete".format(session_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "completed")

    def test_abandon_endpoint_marks_inflight_session(self):
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
            "/runtime/sessions/{0}/abandon".format(session_id),
            json={"abandon_reason": "explicit_exit"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "abandoned")

    def test_hint_endpoint_appends_support_event_without_changing_state(self):
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
            "/runtime/sessions/{0}/hint".format(session_id),
            json={"hint_level": 1, "reason": "need_more_guidance"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "awaiting_answer")
        self.assertEqual(response.json()["hint_count_for_unit"], 1)

    def test_reveal_endpoint_rejects_disallowed_units(self):
        start_response = self.client.post(
            "/runtime/sessions/manual-start",
            json={
                "user_id": "user-1",
                "mode": "Practice",
                "session_intent": "Remediate",
                "unit_id": "elu.concept_recall.practice.remediate.concept.alpha-topic",
            },
        )
        session_id = start_response.json()["session_id"]

        response = self.client.post(
            "/runtime/sessions/{0}/reveal".format(session_id),
            json={"reveal_kind": "canonical_answer"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("answer reveal", response.json()["detail"])

    def test_evaluate_endpoint_returns_409_from_wrong_state(self):
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

        response = self.client.post("/runtime/sessions/{0}/evaluate".format(session_id))

        self.assertEqual(response.status_code, 409)

    def test_get_review_endpoint_returns_404_for_unknown_session(self):
        response = self.client.get("/runtime/sessions/session.missing/review")

        self.assertEqual(response.status_code, 404)

    def test_invalid_submission_kind_returns_400_and_preserves_session(self):
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
                "submission_kind": "auto_submit",
            },
        )
        session_response = self.client.get("/runtime/sessions/{0}".format(session_id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response.json()["state"], "awaiting_answer")
        self.assertEqual(len(session_response.json()["event_ids"]), 3)

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
