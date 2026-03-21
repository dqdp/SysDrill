import copy
import unittest
from pathlib import Path
from typing import Any

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.learner_projection import LearnerProjector
from sysdrill_backend.rule_first_evaluator import evaluate_concept_recall
from sysdrill_backend.session_runtime import SessionRuntime


class StubRuntimeReader:
    def __init__(
        self,
        sessions: list[dict[str, Any]],
        events_by_session: dict[str, list[dict[str, Any]]],
    ):
        self._sessions = copy.deepcopy(sessions)
        self._events_by_session = copy.deepcopy(events_by_session)

    def list_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        sessions = [session for session in self._sessions if session["user_id"] == user_id]
        sessions.sort(key=lambda session: session["session_id"])
        return copy.deepcopy(sessions)

    def list_session_events(self, session_id: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events_by_session.get(session_id, []))


class LearnerProjectorRuleTest(unittest.TestCase):
    def setUp(self):
        self.projector = LearnerProjector()

    def test_build_profile_returns_unknown_biased_empty_profile_without_reviewed_sessions(self):
        profile = self.projector.build_profile(StubRuntimeReader([], {}), user_id="user-1")

        self.assertEqual(
            profile,
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
            },
        )
        self.assertNotIn("current_stage", profile)

    def test_repeated_reviewed_outcomes_increase_concept_confidence(self):
        sessions = [
            reviewed_session(
                session_id="session.0001",
                mode="Study",
                content_id="concept.alpha-topic",
                event_ids=["event.0001", "event.0002"],
                evaluation_result=evaluation_result(
                    session_id="session.0001",
                    weighted_score=0.76,
                    overall_confidence=0.72,
                    concept_explanation_band=2,
                    usage_judgment_band=2,
                    tradeoff_band=2,
                    communication_band=2,
                    hint_dependency=0.0,
                ),
            ),
            reviewed_session(
                session_id="session.0002",
                mode="Study",
                content_id="concept.alpha-topic",
                event_ids=["event.0003", "event.0004"],
                evaluation_result=evaluation_result(
                    session_id="session.0002",
                    weighted_score=0.83,
                    overall_confidence=0.8,
                    concept_explanation_band=3,
                    usage_judgment_band=2,
                    tradeoff_band=2,
                    communication_band=2,
                    hint_dependency=0.0,
                ),
            ),
        ]
        events = {
            "session.0001": session_events(
                session_id="session.0001",
                content_id="concept.alpha-topic",
                occurred_at_values=["2026-03-17T10:00:00Z", "2026-03-17T10:05:00Z"],
            ),
            "session.0002": session_events(
                session_id="session.0002",
                content_id="concept.alpha-topic",
                occurred_at_values=["2026-03-18T10:00:00Z", "2026-03-18T10:05:00Z"],
            ),
        }

        repeated_profile = self.projector.build_profile(
            StubRuntimeReader(sessions, events),
            user_id="user-1",
        )
        single_profile = self.projector.build_profile(
            StubRuntimeReader([sessions[0]], {"session.0001": events["session.0001"]}),
            user_id="user-1",
        )

        repeated_concept = repeated_profile["concept_state"]["concept.alpha-topic"]
        single_concept = single_profile["concept_state"]["concept.alpha-topic"]

        self.assertGreater(
            repeated_concept["confidence"],
            single_concept["confidence"],
        )
        self.assertGreaterEqual(
            repeated_concept["proficiency_estimate"],
            single_concept["proficiency_estimate"],
        )
        self.assertEqual(repeated_concept["last_evidence_at"], "2026-03-18T10:05:00Z")

    def test_support_dependence_dampens_positive_evidence(self):
        strong_independent = reviewed_session(
            session_id="session.0010",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0010"],
            evaluation_result=evaluation_result(
                session_id="session.0010",
                weighted_score=0.8,
                overall_confidence=0.8,
                concept_explanation_band=3,
                usage_judgment_band=2,
                tradeoff_band=2,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )
        supported = reviewed_session(
            session_id="session.0011",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0011"],
            evaluation_result=evaluation_result(
                session_id="session.0011",
                weighted_score=0.8,
                overall_confidence=0.8,
                concept_explanation_band=3,
                usage_judgment_band=2,
                tradeoff_band=2,
                communication_band=2,
                hint_dependency=0.55,
            ),
        )

        events = {
            "session.0010": session_events(
                session_id="session.0010",
                content_id="concept.alpha-topic",
                occurred_at_values=["2026-03-17T11:00:00Z"],
            ),
            "session.0011": session_events(
                session_id="session.0011",
                content_id="concept.alpha-topic",
                occurred_at_values=["2026-03-17T11:05:00Z"],
            ),
        }

        independent_profile = self.projector.build_profile(
            StubRuntimeReader([strong_independent], {"session.0010": events["session.0010"]}),
            user_id="user-1",
        )
        supported_profile = self.projector.build_profile(
            StubRuntimeReader([supported], {"session.0011": events["session.0011"]}),
            user_id="user-1",
        )

        independent_concept = independent_profile["concept_state"]["concept.alpha-topic"]
        supported_concept = supported_profile["concept_state"]["concept.alpha-topic"]

        self.assertGreater(
            independent_concept["proficiency_estimate"],
            supported_concept["proficiency_estimate"],
        )
        self.assertGreater(independent_concept["confidence"], supported_concept["confidence"])
        self.assertGreater(
            supported_concept["hint_dependency_signal"],
            independent_concept["hint_dependency_signal"],
        )
        self.assertGreater(
            supported_concept["review_due_risk"],
            independent_concept["review_due_risk"],
        )

    def test_practice_weights_supported_subskills_more_than_study(self):
        study_session = reviewed_session(
            session_id="session.0020",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0020"],
            evaluation_result=evaluation_result(
                session_id="session.0020",
                weighted_score=0.75,
                overall_confidence=0.75,
                concept_explanation_band=2,
                usage_judgment_band=2,
                tradeoff_band=3,
                communication_band=3,
                hint_dependency=0.0,
            ),
        )
        practice_session = reviewed_session(
            session_id="session.0021",
            mode="Practice",
            content_id="concept.alpha-topic",
            event_ids=["event.0021"],
            evaluation_result=evaluation_result(
                session_id="session.0021",
                weighted_score=0.75,
                overall_confidence=0.75,
                concept_explanation_band=2,
                usage_judgment_band=2,
                tradeoff_band=3,
                communication_band=3,
                hint_dependency=0.0,
            ),
        )

        study_profile = self.projector.build_profile(
            StubRuntimeReader(
                [study_session],
                {
                    "session.0020": session_events(
                        session_id="session.0020",
                        content_id="concept.alpha-topic",
                        occurred_at_values=["2026-03-17T12:00:00Z"],
                    ),
                },
            ),
            user_id="user-1",
        )
        practice_profile = self.projector.build_profile(
            StubRuntimeReader(
                [practice_session],
                {
                    "session.0021": session_events(
                        session_id="session.0021",
                        content_id="concept.alpha-topic",
                        occurred_at_values=["2026-03-17T12:05:00Z"],
                    ),
                },
            ),
            user_id="user-1",
        )

        self.assertGreater(
            practice_profile["subskill_state"]["tradeoff_reasoning"]["proficiency_estimate"],
            study_profile["subskill_state"]["tradeoff_reasoning"]["proficiency_estimate"],
        )
        self.assertGreater(
            practice_profile["subskill_state"]["communication_clarity"]["proficiency_estimate"],
            study_profile["subskill_state"]["communication_clarity"]["proficiency_estimate"],
        )

    def test_review_due_risk_reflects_recency_plus_fragility(self):
        fragile_old = reviewed_session(
            session_id="session.0030",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0030"],
            evaluation_result=evaluation_result(
                session_id="session.0030",
                weighted_score=0.45,
                overall_confidence=0.6,
                concept_explanation_band=1,
                usage_judgment_band=1,
                tradeoff_band=1,
                communication_band=2,
                hint_dependency=0.35,
            ),
        )
        strong_recent = reviewed_session(
            session_id="session.0031",
            mode="Study",
            content_id="concept.beta-topic",
            event_ids=["event.0031"],
            evaluation_result=evaluation_result(
                session_id="session.0031",
                weighted_score=0.82,
                overall_confidence=0.8,
                concept_explanation_band=3,
                usage_judgment_band=2,
                tradeoff_band=2,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )

        profile = self.projector.build_profile(
            StubRuntimeReader(
                [fragile_old, strong_recent],
                {
                    "session.0030": session_events(
                        session_id="session.0030",
                        content_id="concept.alpha-topic",
                        occurred_at_values=["2026-03-10T10:00:00Z"],
                    ),
                    "session.0031": session_events(
                        session_id="session.0031",
                        content_id="concept.beta-topic",
                        occurred_at_values=["2026-03-18T10:00:00Z"],
                    ),
                },
            ),
            user_id="user-1",
        )

        self.assertGreater(
            profile["concept_state"]["concept.alpha-topic"]["review_due_risk"],
            profile["concept_state"]["concept.beta-topic"]["review_due_risk"],
        )

    def test_review_due_risk_grows_with_wall_clock_inactivity(self):
        session = reviewed_session(
            session_id="session.0035",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0035"],
            evaluation_result=evaluation_result(
                session_id="session.0035",
                weighted_score=0.82,
                overall_confidence=0.8,
                concept_explanation_band=3,
                usage_judgment_band=2,
                tradeoff_band=2,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )
        runtime = StubRuntimeReader(
            [session],
            {
                "session.0035": session_events(
                    session_id="session.0035",
                    content_id="concept.alpha-topic",
                    occurred_at_values=["2026-03-01T10:00:00Z"],
                ),
            },
        )

        fresh_profile = self.projector.build_profile(
            runtime,
            user_id="user-1",
            now="2026-03-01T10:00:00Z",
        )
        stale_profile = self.projector.build_profile(
            runtime,
            user_id="user-1",
            now="2026-03-21T10:00:00Z",
        )

        self.assertGreater(
            stale_profile["concept_state"]["concept.alpha-topic"]["review_due_risk"],
            fresh_profile["concept_state"]["concept.alpha-topic"]["review_due_risk"],
        )

    def test_reviewed_evidence_time_ignores_late_session_completion_for_concepts_and_subskills(
        self,
    ):
        completed_session = reviewed_session(
            session_id="session.0035a",
            mode="Practice",
            content_id="concept.alpha-topic",
            event_ids=["event.0035a"],
            evaluation_result=evaluation_result(
                session_id="session.0035a",
                weighted_score=0.76,
                overall_confidence=0.74,
                concept_explanation_band=2,
                usage_judgment_band=2,
                tradeoff_band=3,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )
        open_review_session = reviewed_session(
            session_id="session.0035b",
            mode="Practice",
            content_id="concept.alpha-topic",
            event_ids=["event.0035b"],
            evaluation_result=evaluation_result(
                session_id="session.0035b",
                weighted_score=0.76,
                overall_confidence=0.74,
                concept_explanation_band=2,
                usage_judgment_band=2,
                tradeoff_band=3,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )

        completed_profile = self.projector.build_profile(
            StubRuntimeReader(
                [completed_session],
                {
                    "session.0035a": session_events(
                        session_id="session.0035a",
                        content_id="concept.alpha-topic",
                        occurred_at_values=[
                            "2026-03-20T10:00:00Z",
                            "2026-03-20T10:01:00Z",
                            "2026-03-25T10:00:00Z",
                        ],
                        event_types=[
                            "evaluation_attached",
                            "review_presented",
                            "session_completed",
                        ],
                    ),
                },
            ),
            user_id="user-1",
            now="2026-03-27T10:00:00Z",
        )
        open_review_profile = self.projector.build_profile(
            StubRuntimeReader(
                [open_review_session],
                {
                    "session.0035b": session_events(
                        session_id="session.0035b",
                        content_id="concept.alpha-topic",
                        occurred_at_values=[
                            "2026-03-20T10:00:00Z",
                            "2026-03-20T10:01:00Z",
                        ],
                        event_types=[
                            "evaluation_attached",
                            "review_presented",
                        ],
                    ),
                },
            ),
            user_id="user-1",
            now="2026-03-27T10:00:00Z",
        )

        self.assertEqual(
            completed_profile["concept_state"]["concept.alpha-topic"]["last_evidence_at"],
            "2026-03-20T10:00:00Z",
        )
        self.assertEqual(
            completed_profile["subskill_state"]["tradeoff_reasoning"]["last_evidence_at"],
            "2026-03-20T10:00:00Z",
        )
        self.assertEqual(
            completed_profile["concept_state"]["concept.alpha-topic"]["review_due_risk"],
            open_review_profile["concept_state"]["concept.alpha-topic"]["review_due_risk"],
        )
        self.assertEqual(
            completed_profile["trajectory_state"]["last_active_at"],
            "2026-03-25T10:00:00Z",
        )

    def test_reviewed_mock_subskill_recency_uses_evaluation_time_not_completion_time(self):
        mock_session = reviewed_mock_session(
            session_id="session.0035c",
            scenario_id="scenario.url-shortener.basic",
            bound_concept_ids=["concept.url-shortener.storage-choice"],
            event_ids=["event.0035c"],
            evaluation_result=url_shortener_evaluation_result(
                session_id="session.0035c",
                weighted_score=0.74,
                overall_confidence=0.72,
                requirements_band=2,
                decomposition_band=2,
                storage_band=2,
                scaling_band=2,
                reliability_band=2,
                tradeoff_band=3,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )

        profile = self.projector.build_profile(
            StubRuntimeReader(
                [mock_session],
                {
                    "session.0035c": session_events(
                        session_id="session.0035c",
                        content_id="scenario.url-shortener.basic",
                        occurred_at_values=[
                            "2026-03-20T11:00:00Z",
                            "2026-03-20T11:01:00Z",
                            "2026-03-23T11:00:00Z",
                        ],
                        event_types=[
                            "evaluation_attached",
                            "review_presented",
                            "session_completed",
                        ],
                    ),
                },
            ),
            user_id="user-1",
            now="2026-03-27T11:00:00Z",
        )

        self.assertEqual(profile["concept_state"], {})
        self.assertEqual(
            profile["subskill_state"]["tradeoff_reasoning"]["last_evidence_at"],
            "2026-03-20T11:00:00Z",
        )
        self.assertEqual(
            profile["trajectory_state"]["last_active_at"],
            "2026-03-23T11:00:00Z",
        )

    def test_reviewed_evidence_time_falls_back_without_semantic_review_events(self):
        session = reviewed_session(
            session_id="session.0035d",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0035d"],
            evaluation_result=evaluation_result(
                session_id="session.0035d",
                weighted_score=0.7,
                overall_confidence=0.68,
                concept_explanation_band=2,
                usage_judgment_band=2,
                tradeoff_band=2,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )

        profile = self.projector.build_profile(
            StubRuntimeReader(
                [session],
                {
                    "session.0035d": session_events(
                        session_id="session.0035d",
                        content_id="concept.alpha-topic",
                        occurred_at_values=[
                            "2026-03-20T12:00:00Z",
                            "2026-03-20T12:07:00Z",
                        ],
                        event_types=[
                            "session_started",
                            "session_completed",
                        ],
                    ),
                },
            ),
            user_id="user-1",
            now="2026-03-27T12:00:00Z",
        )

        self.assertEqual(
            profile["concept_state"]["concept.alpha-topic"]["last_evidence_at"],
            "2026-03-20T12:07:00Z",
        )

    def test_mock_scenario_evidence_stays_out_of_concept_state_until_richer_mapping_exists(
        self,
    ):
        bound_concept_id = "concept.url-shortener.storage-choice"
        mock_session = reviewed_mock_session(
            session_id="session.0036",
            scenario_id="scenario.url-shortener.basic",
            bound_concept_ids=[bound_concept_id],
            event_ids=["event.0036"],
            evaluation_result=url_shortener_evaluation_result(
                session_id="session.0036",
                weighted_score=0.82,
                overall_confidence=0.8,
                requirements_band=3,
                decomposition_band=3,
                storage_band=3,
                scaling_band=2,
                reliability_band=2,
                tradeoff_band=3,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )
        direct_session = reviewed_session(
            session_id="session.0037",
            mode="Study",
            content_id=bound_concept_id,
            event_ids=["event.0037"],
            evaluation_result=evaluation_result(
                session_id="session.0037",
                weighted_score=0.82,
                overall_confidence=0.8,
                concept_explanation_band=3,
                usage_judgment_band=3,
                tradeoff_band=3,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )

        mock_profile = self.projector.build_profile(
            StubRuntimeReader(
                [mock_session],
                {
                    "session.0036": session_events(
                        session_id="session.0036",
                        content_id="scenario.url-shortener.basic",
                        occurred_at_values=["2026-03-20T10:00:00Z"],
                    ),
                },
            ),
            user_id="user-1",
        )
        direct_profile = self.projector.build_profile(
            StubRuntimeReader(
                [direct_session],
                {
                    "session.0037": session_events(
                        session_id="session.0037",
                        content_id=bound_concept_id,
                        occurred_at_values=["2026-03-20T10:05:00Z"],
                    ),
                },
            ),
            user_id="user-1",
        )

        self.assertEqual(mock_profile["concept_state"], {})
        self.assertIn(bound_concept_id, direct_profile["concept_state"])
        self.assertGreater(
            mock_profile["subskill_state"]["tradeoff_reasoning"]["proficiency_estimate"],
            0.0,
        )
        self.assertGreater(
            mock_profile["trajectory_state"]["mock_readiness_estimate"],
            0.0,
        )

    def test_mock_readiness_remains_conservative_without_mock_or_follow_up_evidence(self):
        profile = self.projector.build_profile(
            StubRuntimeReader(
                [
                    reviewed_session(
                        session_id="session.0040",
                        mode="Practice",
                        content_id="concept.alpha-topic",
                        event_ids=["event.0040"],
                        evaluation_result=evaluation_result(
                            session_id="session.0040",
                            weighted_score=0.85,
                            overall_confidence=0.82,
                            concept_explanation_band=3,
                            usage_judgment_band=3,
                            tradeoff_band=3,
                            communication_band=3,
                            hint_dependency=0.0,
                        ),
                    ),
                ],
                {
                    "session.0040": session_events(
                        session_id="session.0040",
                        content_id="concept.alpha-topic",
                        occurred_at_values=["2026-03-18T11:00:00Z"],
                    ),
                },
            ),
            user_id="user-1",
        )

        self.assertLessEqual(profile["trajectory_state"]["mock_readiness_estimate"], 0.45)
        self.assertLessEqual(profile["trajectory_state"]["mock_readiness_confidence"], 0.35)

    def test_abandonment_events_raise_trajectory_signals_without_claiming_knowledge_failure(self):
        profile = self.projector.build_profile(
            StubRuntimeReader(
                [
                    abandoned_session(
                        session_id="session.0045",
                        mode="Study",
                        content_id="concept.alpha-topic",
                        event_ids=["event.0045"],
                    ),
                ],
                {
                    "session.0045": session_events(
                        session_id="session.0045",
                        content_id="concept.alpha-topic",
                        event_types=["session_abandoned"],
                        occurred_at_values=["2026-03-18T11:05:00Z"],
                        payloads=[{"abandon_reason": "explicit_exit"}],
                    ),
                },
            ),
            user_id="user-1",
        )

        self.assertEqual(profile["concept_state"], {})
        self.assertGreater(profile["trajectory_state"]["recent_abandonment_signal"], 0.0)
        self.assertGreater(profile["trajectory_state"]["recent_fatigue_signal"], 0.0)

    def test_profile_output_is_deterministic_and_uses_canonical_keys(self):
        session = reviewed_session(
            session_id="session.0050",
            mode="Study",
            content_id="concept.alpha-topic",
            event_ids=["event.0050", "event.0051"],
            evaluation_result=evaluation_result(
                session_id="session.0050",
                weighted_score=0.78,
                overall_confidence=0.76,
                concept_explanation_band=2,
                usage_judgment_band=3,
                tradeoff_band=2,
                communication_band=2,
                hint_dependency=0.0,
            ),
        )
        runtime = StubRuntimeReader(
            [session],
            {
                "session.0050": session_events(
                    session_id="session.0050",
                    content_id="concept.alpha-topic",
                    occurred_at_values=["2026-03-17T09:00:00Z", "2026-03-17T09:05:00Z"],
                ),
            },
        )

        first = self.projector.build_profile(runtime, user_id="user-1")
        second = self.projector.build_profile(runtime, user_id="user-1")

        self.assertEqual(first, second)
        self.assertIn("concept.alpha-topic", first["concept_state"])
        self.assertNotIn("current_stage", first)
        self.assertNotIn("constraint_discovery", first["subskill_state"])
        self.assertEqual(first["last_updated_at"], "2026-03-17T09:05:00Z")


class LearnerProjectorIntegrationTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.catalog = load_topic_catalog(export_root, allow_draft_bundles=True)
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"
        self.mock_unit_id = (
            "elu.scenario_readiness_check.mock_interview.readiness_check."
            "scenario.url-shortener.basic"
        )

    def test_runtime_exposes_user_sessions_for_projection(self):
        runtime = SessionRuntime(self.catalog)
        runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        runtime.start_manual_session(
            user_id="user-2",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        sessions = runtime.list_user_sessions("user-1")

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["user_id"], "user-1")
        self.assertEqual(sessions[0]["current_unit"]["id"], self.study_unit_id)

    def test_projector_builds_profile_from_real_runtime_history(self):
        runtime = SessionRuntime(self.catalog)
        projector = LearnerProjector()
        session = runtime.start_manual_session(
            user_id="user-1",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "Caching stores frequently used data in a faster layer. "
                "Use it for read-heavy or latency-sensitive paths, but stale data "
                "and invalidation complexity are trade-offs."
            ),
            response_modality="text",
            submission_kind="manual_submit",
            response_latency_ms=42000,
        )
        runtime.evaluate_pending_session(session["session_id"])

        profile = projector.build_profile(runtime, user_id="user-1")

        concept = profile["concept_state"]["concept.alpha-topic"]
        self.assertGreater(concept["proficiency_estimate"], 0.0)
        self.assertGreater(concept["confidence"], 0.0)
        self.assertEqual(concept["hint_dependency_signal"], 0.0)
        self.assertIn("tradeoff_reasoning", profile["subskill_state"])
        self.assertIn("communication_clarity", profile["subskill_state"])
        self.assertIsNotNone(profile["last_updated_at"])
        self.assertEqual(profile, projector.build_profile(runtime, user_id="user-1"))

    def test_projector_uses_custom_evaluation_support_signals_from_runtime_history(self):
        runtime = SessionRuntime(self.catalog, evaluator=evaluator_with_hint_dependency(0.55))
        projector = LearnerProjector()
        session = runtime.start_manual_session(
            user_id="user-1",
            mode="Practice",
            session_intent="Remediate",
            unit_id="elu.concept_recall.practice.remediate.concept.alpha-topic",
        )
        runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Caching stores data for faster repeated access.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        runtime.evaluate_pending_session(session["session_id"])

        profile = projector.build_profile(runtime, user_id="user-1")

        concept = profile["concept_state"]["concept.alpha-topic"]
        self.assertGreater(concept["hint_dependency_signal"], 0.0)
        self.assertGreater(concept["review_due_risk"], 0.0)

    def test_projector_keeps_reviewed_mock_history_out_of_concept_state(self):
        runtime = SessionRuntime(self.catalog)
        projector = LearnerProjector()
        session = runtime.start_manual_session(
            user_id="user-1",
            mode="MockInterview",
            session_intent="ReadinessCheck",
            unit_id=self.mock_unit_id,
        )
        runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "I would start with redirect reads, durable mapping storage, "
                "and short-id generation because the service is read-heavy."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "I would use a counter or random-id strategy with collision checks "
                "and cache the redirect path."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        runtime.evaluate_pending_session(session["session_id"])

        profile = projector.build_profile(runtime, user_id="user-1")

        self.assertEqual(profile["concept_state"], {})
        self.assertIn("tradeoff_reasoning", profile["subskill_state"])
        self.assertIn("communication_clarity", profile["subskill_state"])
        self.assertGreater(profile["trajectory_state"]["mock_readiness_estimate"], 0.0)
        self.assertGreater(profile["trajectory_state"]["mock_readiness_confidence"], 0.0)

    def test_projector_treats_abandoned_mock_as_trajectory_only_signal(self):
        runtime = SessionRuntime(self.catalog)
        projector = LearnerProjector()
        session = runtime.start_manual_session(
            user_id="user-1",
            mode="MockInterview",
            session_intent="ReadinessCheck",
            unit_id=self.mock_unit_id,
        )
        runtime.abandon_session(session["session_id"], abandon_reason="explicit_exit")

        profile = projector.build_profile(runtime, user_id="user-1")

        self.assertEqual(profile["concept_state"], {})
        self.assertEqual(profile["subskill_state"], {})
        self.assertGreater(profile["trajectory_state"]["recent_abandonment_signal"], 0.0)
        self.assertGreater(profile["trajectory_state"]["recent_fatigue_signal"], 0.0)


def reviewed_session(
    session_id: str,
    mode: str,
    content_id: str,
    event_ids: list[str],
    evaluation_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "user_id": "user-1",
        "mode": mode,
        "session_intent": "LearnNew" if mode == "Study" else "Remediate",
        "strictness_profile": "supportive" if mode == "Study" else "standard",
        "state": "review_presented",
        "planned_unit_ids": [
            "elu.concept_recall.{0}.learn_new.{1}".format(mode.lower(), content_id)
        ],
        "current_unit": {
            "id": "elu.concept_recall.{0}.learn_new.{1}".format(mode.lower(), content_id),
            "source_content_ids": [content_id],
            "evaluation_binding_id": "binding.concept_recall.v1",
            "visible_prompt": "Explain it.",
        },
        "event_ids": list(event_ids),
        "last_evaluation_result": copy.deepcopy(evaluation_result),
        "last_review_report": {"linked_evaluation_ids": [evaluation_result["evaluation_id"]]},
        "recommendation_decision_id": None,
    }


def abandoned_session(
    session_id: str,
    mode: str,
    content_id: str,
    event_ids: list[str],
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "user_id": "user-1",
        "mode": mode,
        "session_intent": "LearnNew" if mode == "Study" else "Remediate",
        "strictness_profile": "supportive" if mode == "Study" else "standard",
        "state": "abandoned",
        "planned_unit_ids": [
            "elu.concept_recall.{0}.learn_new.{1}".format(mode.lower(), content_id)
        ],
        "current_unit": {
            "id": "elu.concept_recall.{0}.learn_new.{1}".format(mode.lower(), content_id),
            "source_content_ids": [content_id],
            "evaluation_binding_id": "binding.concept_recall.v1",
            "visible_prompt": "Explain it.",
        },
        "event_ids": list(event_ids),
        "last_evaluation_result": None,
        "last_review_report": None,
        "recommendation_decision_id": None,
    }


def reviewed_mock_session(
    session_id: str,
    scenario_id: str,
    bound_concept_ids: list[str],
    event_ids: list[str],
    evaluation_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "user_id": "user-1",
        "mode": "MockInterview",
        "session_intent": "ReadinessCheck",
        "strictness_profile": "strict",
        "state": "review_presented",
        "planned_unit_ids": [
            ("elu.scenario_readiness_check.mock_interview.readiness_check.{0}".format(scenario_id))
        ],
        "current_unit": {
            "id": (
                "elu.scenario_readiness_check.mock_interview.readiness_check.{0}".format(
                    scenario_id
                )
            ),
            "unit_family": "scenario_readiness_check",
            "source_content_ids": [scenario_id],
            "bound_concept_ids": list(bound_concept_ids),
            "scenario_family": "url_shortener",
            "evaluation_binding_id": "binding.url_shortener.v1",
            "visible_prompt": "Design it.",
        },
        "event_ids": list(event_ids),
        "last_evaluation_result": copy.deepcopy(evaluation_result),
        "last_review_report": {"linked_evaluation_ids": [evaluation_result["evaluation_id"]]},
        "recommendation_decision_id": None,
    }


def evaluation_result(
    session_id: str,
    weighted_score: float,
    overall_confidence: float,
    concept_explanation_band: int,
    usage_judgment_band: int,
    tradeoff_band: int,
    communication_band: int,
    hint_dependency: float,
) -> dict[str, Any]:
    return {
        "evaluation_id": "evaluation.{0}".format(session_id),
        "session_id": session_id,
        "unit_id": "unit.{0}".format(session_id),
        "binding_id": "binding.concept_recall.v1",
        "criterion_results": [
            criterion_result("concept_explanation", concept_explanation_band, 0.72),
            criterion_result("usage_judgment", usage_judgment_band, 0.74),
            criterion_result("trade_off_articulation", tradeoff_band, 0.76),
            criterion_result("communication_clarity", communication_band, 0.78),
        ],
        "gating_failures": [],
        "weighted_score": weighted_score,
        "overall_confidence": overall_confidence,
        "missing_dimensions": [],
        "review_summary": {},
        "summary_feedback": {},
        "downstream_signals": {
            "coverage_gap": round(max(0.0, (3 - concept_explanation_band) / 3.0), 4),
            "usage_gap": round(max(0.0, (3 - usage_judgment_band) / 3.0), 4),
            "tradeoff_gap": round(max(0.0, (3 - tradeoff_band) / 3.0), 4),
            "communication_gap": round(max(0.0, (3 - communication_band) / 3.0), 4),
            "hint_dependency": hint_dependency,
            "strong_independent_performance": bool(
                weighted_score >= 0.75 and overall_confidence >= 0.7 and hint_dependency == 0.0
            ),
        },
        "rubric_version": "rubric.v1",
        "rubric_version_ref": "rubric.v1",
        "binding_version_ref": "binding.concept_recall.v1",
        "evaluation_mode": "rule_only",
        "evaluator_version_ref": "rule_first.concept_recall.v1",
    }


def url_shortener_evaluation_result(
    session_id: str,
    weighted_score: float,
    overall_confidence: float,
    requirements_band: int,
    decomposition_band: int,
    storage_band: int,
    scaling_band: int,
    reliability_band: int,
    tradeoff_band: int,
    communication_band: int,
    hint_dependency: float,
) -> dict[str, Any]:
    return {
        "evaluation_id": "evaluation.{0}".format(session_id),
        "session_id": session_id,
        "unit_id": "unit.{0}".format(session_id),
        "binding_id": "binding.url_shortener.v1",
        "criterion_results": [
            criterion_result("requirements_understanding", requirements_band, 0.74),
            criterion_result("decomposition_quality", decomposition_band, 0.76),
            criterion_result("data_and_storage_choices", storage_band, 0.78),
            criterion_result("scaling_strategy", scaling_band, 0.76),
            criterion_result("reliability_awareness", reliability_band, 0.72),
            criterion_result("trade_off_articulation", tradeoff_band, 0.78),
            criterion_result("communication_clarity", communication_band, 0.74),
        ],
        "gating_failures": [],
        "weighted_score": weighted_score,
        "overall_confidence": overall_confidence,
        "missing_dimensions": [],
        "review_summary": {},
        "summary_feedback": {},
        "downstream_signals": {
            "hint_dependency": hint_dependency,
            "strong_independent_performance": bool(
                weighted_score >= 0.75 and overall_confidence >= 0.7 and hint_dependency == 0.0
            ),
        },
        "rubric_version": "rubric.v1",
        "rubric_version_ref": "rubric.v1",
        "binding_version_ref": "binding.url_shortener.v1",
        "evaluation_mode": "rule_only",
        "evaluator_version_ref": "rule_first.url_shortener.v1",
    }


def criterion_result(
    criterion_id: str,
    score_band: int,
    criterion_confidence: float,
) -> dict[str, Any]:
    return {
        "criterion_id": criterion_id,
        "applicability": "required",
        "weight": 1.0,
        "score_band": score_band,
        "observed_evidence": [],
        "missing_aspects": [],
        "inferred_judgment": "",
        "criterion_confidence": criterion_confidence,
    }


def session_events(
    session_id: str,
    content_id: str,
    occurred_at_values: list[str],
    event_types: list[str] | None = None,
    payloads: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    resolved_event_types = event_types or [
        "review_presented" if index == len(occurred_at_values) - 1 else "session_started"
        for index in range(len(occurred_at_values))
    ]
    resolved_payloads = payloads or [{} for _ in occurred_at_values]
    return [
        {
            "event_id": "event.{0}.{1}".format(session_id, index),
            "event_type": resolved_event_types[index],
            "user_id": "user-1",
            "session_id": session_id,
            "mode": "Study",
            "session_intent": "LearnNew",
            "content_id": content_id,
            "occurred_at": occurred_at,
            "payload": resolved_payloads[index],
            "source": "web",
            "trace_id": "trace.{0}".format(session_id),
        }
        for index, occurred_at in enumerate(occurred_at_values)
    ]


def evaluator_with_hint_dependency(hint_dependency: float):
    def evaluate(request: dict[str, Any]) -> dict[str, Any]:
        bundle = evaluate_concept_recall(request)
        bundle["evaluation_result"]["downstream_signals"]["hint_dependency"] = hint_dependency
        bundle["review_report"]["support_dependence_note"] = (
            "Support usage lowers confidence in fully independent recall for this attempt."
        )
        return bundle

    return evaluate
