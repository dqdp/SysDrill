import copy
import unittest
from pathlib import Path

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.recommendation_engine import (
    NoRecommendationCandidatesError,
    RecommendationDecisionLifecycleError,
    RecommendationDecisionNotFoundError,
    RecommendationEngine,
)
from sysdrill_backend.session_runtime import SessionRuntime


def _strong_transcript() -> str:
    return (
        "Caching is storing frequently accessed data in a faster layer. "
        "Use it for read-heavy or latency-sensitive paths. The trade-offs are "
        "stale data, invalidation complexity, and extra memory cost."
    )


def _weak_transcript() -> str:
    return "Caching is keeping data somewhere faster."


class RecommendationEngineTest(unittest.TestCase):
    def setUp(self):
        export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.catalog = load_topic_catalog(export_root, allow_draft_bundles=True)
        self.runtime = SessionRuntime(self.catalog)
        self.engine = RecommendationEngine(self.runtime)
        self.study_unit_id = "elu.concept_recall.study.learn_new.concept.alpha-topic"
        self.mock_unit_id = (
            "elu.scenario_readiness_check.mock_interview.readiness_check."
            "scenario.url-shortener.basic"
        )

    def test_next_recommendation_prefers_study_learn_new_when_no_reviewed_history_exists(self):
        decision = self.engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["policy_version"], "bootstrap.recommendation.v1")
        self.assertEqual(decision["decision_mode"], "rule_based")
        self.assertEqual(
            decision["candidate_actions"],
            [
                {
                    "mode": "Study",
                    "session_intent": "LearnNew",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "introductory",
                    "strictness_profile": "supportive",
                    "session_size": "single_unit",
                    "delivery_profile": "text_first",
                },
                {
                    "mode": "Study",
                    "session_intent": "Reinforce",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "standard",
                    "strictness_profile": "supportive",
                    "session_size": "single_unit",
                    "delivery_profile": "text_first",
                },
                {
                    "mode": "Study",
                    "session_intent": "SpacedReview",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "standard",
                    "strictness_profile": "supportive",
                    "session_size": "single_unit",
                    "delivery_profile": "text_first",
                },
            ],
        )
        self.assertEqual(
            decision["chosen_action"],
            {
                "mode": "Study",
                "session_intent": "LearnNew",
                "target_type": "concept",
                "target_id": "concept.alpha-topic",
                "difficulty_profile": "introductory",
                "strictness_profile": "supportive",
                "session_size": "single_unit",
                "delivery_profile": "text_first",
                "rationale": (
                    "Start with a supportive Study / LearnNew unit on "
                    "'Кэширование' because there is no reviewed evidence for "
                    "this concept yet."
                ),
            },
        )
        self.assertEqual(
            decision["supporting_signals"],
            [
                "no_prior_reviewed_attempt_for_target",
                "bootstrap_exploration_bias",
            ],
        )
        self.assertEqual(decision["blocking_signals"], [])
        self.assertNotIn("unit_id", decision["chosen_action"])

    def test_next_recommendation_prefers_remediation_for_weak_reviewed_outcome(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=_weak_transcript(),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        decision = self.engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Practice")
        self.assertEqual(decision["chosen_action"]["session_intent"], "Remediate")
        self.assertEqual(decision["chosen_action"]["target_id"], "concept.alpha-topic")
        self.assertEqual(
            decision["supporting_signals"],
            [
                "weak_reviewed_outcome",
                "bounded_remediation_priority",
            ],
        )
        self.assertIn("remediate", decision["rationale"].lower())

    def test_next_recommendation_falls_back_to_spaced_review_after_strong_reviewed_outcome(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=_strong_transcript(),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        decision = self.engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Study")
        self.assertEqual(decision["chosen_action"]["session_intent"], "SpacedReview")
        self.assertEqual(
            decision["supporting_signals"],
            [
                "reviewed_success_without_unseen_targets",
                "bounded_spaced_review_fallback",
            ],
        )
        self.assertIn("review", decision["rationale"].lower())

    def test_next_recommendation_prefers_reinforcement_when_projected_subskill_is_still_weak(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=_strong_transcript(),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.74,
                            "confidence": 0.66,
                            "review_due_risk": 0.22,
                            "hint_dependency_signal": 0.0,
                            "last_evidence_at": "2026-03-20T10:00:00Z",
                        },
                    },
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.31,
                            "confidence": 0.62,
                            "last_evidence_at": "2026-03-20T10:00:00Z",
                        },
                        "communication_clarity": {
                            "proficiency_estimate": 0.79,
                            "confidence": 0.7,
                            "last_evidence_at": "2026-03-20T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.0,
                        "recent_abandonment_signal": 0.0,
                        "mock_readiness_estimate": 0.2,
                        "mock_readiness_confidence": 0.15,
                        "last_active_at": "2026-03-20T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-20T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Practice")
        self.assertEqual(decision["chosen_action"]["session_intent"], "Reinforce")
        self.assertIn("reinforcement", decision["rationale"].lower())
        self.assertIn("bounded_reinforcement_priority", decision["supporting_signals"])

    def test_next_recommendation_avoids_triple_repeat_of_same_action_pattern(self):
        expanded_catalog = copy.deepcopy(self.catalog)
        beta_topic = copy.deepcopy(expanded_catalog["alpha-topic"])
        beta_topic["topic_package"]["canonical_content"]["concepts"][0]["id"]["value"] = (
            "concept.beta-topic"
        )
        beta_topic["topic_package"]["canonical_content"]["concepts"][0]["title"]["value"] = (
            "Репликация"
        )
        expanded_catalog["beta-topic"] = beta_topic

        runtime = SessionRuntime(expanded_catalog)
        engine = RecommendationEngine(runtime)

        first = engine.next_recommendation(user_id="demo-user")
        engine.mark_accepted(first["decision_id"], session_id="session.0001")
        second = engine.next_recommendation(user_id="demo-user")
        engine.mark_accepted(second["decision_id"], session_id="session.0002")
        third = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(first["chosen_action"]["target_id"], "concept.alpha-topic")
        self.assertEqual(second["chosen_action"]["target_id"], "concept.alpha-topic")
        self.assertEqual(third["chosen_action"]["mode"], "Study")
        self.assertEqual(third["chosen_action"]["session_intent"], "LearnNew")
        self.assertEqual(third["chosen_action"]["target_id"], "concept.beta-topic")
        self.assertIn("anti_loop_guardrail", third["blocking_signals"])
        self.assertFalse(
            any(
                action["mode"] == "Study"
                and action["session_intent"] == "LearnNew"
                and action["target_id"] == "concept.alpha-topic"
                for action in third["candidate_actions"]
            )
        )

    def test_next_recommendation_rejects_empty_candidate_space(self):
        empty_catalog = copy.deepcopy(self.catalog)
        empty_catalog["alpha-topic"]["topic_package"]["learning_design_drafts"][
            "candidate_card_types"
        ] = []
        runtime = SessionRuntime(empty_catalog)
        engine = RecommendationEngine(runtime)

        with self.assertRaisesRegex(
            NoRecommendationCandidatesError,
            "no recommendation candidates",
        ):
            engine.next_recommendation(user_id="demo-user")

    def test_get_unknown_decision_fails_closed(self):
        with self.assertRaisesRegex(RecommendationDecisionNotFoundError, "unknown decision_id"):
            self.engine.get_decision("rec.missing")

    def test_mark_accepted_rejects_second_acceptance_for_same_decision(self):
        decision = self.engine.next_recommendation(user_id="demo-user")

        self.engine.mark_accepted(decision["decision_id"], session_id="session.0001")

        with self.assertRaisesRegex(
            RecommendationDecisionLifecycleError,
            "already accepted",
        ):
            self.engine.mark_accepted(decision["decision_id"], session_id="session.0002")

        stored = self.engine.get_decision(decision["decision_id"])
        self.assertEqual(stored["accepted_session_id"], "session.0001")

    def test_mark_completed_requires_matching_accepted_session(self):
        decision = self.engine.next_recommendation(user_id="demo-user")
        self.engine.mark_accepted(decision["decision_id"], session_id="session.0001")

        with self.assertRaisesRegex(
            RecommendationDecisionLifecycleError,
            "accepted session",
        ):
            self.engine.mark_completed(decision["decision_id"], session_id="session.0002")

        self.engine.mark_completed(decision["decision_id"], session_id="session.0001")
        stored = self.engine.get_decision(decision["decision_id"])
        self.assertEqual(stored["completed_session_id"], "session.0001")

    def test_recent_accepted_patterns_follow_acceptance_time_not_decision_id(self):
        self.engine._decisions = {
            "rec.0001": {
                "user_id": "demo-user",
                "accepted_at": "2026-03-20T10:05:00Z",
                "chosen_action": {
                    "mode": "Study",
                    "session_intent": "LearnNew",
                    "target_id": "concept.alpha-topic",
                },
            },
            "rec.0002": {
                "user_id": "demo-user",
                "accepted_at": "2026-03-20T10:03:00Z",
                "chosen_action": {
                    "mode": "Practice",
                    "session_intent": "Remediate",
                    "target_id": "concept.beta-topic",
                },
            },
        }

        self.assertEqual(
            self.engine._recent_accepted_patterns("demo-user"),
            [
                ("Practice", "Remediate", "concept.beta-topic"),
                ("Study", "LearnNew", "concept.alpha-topic"),
            ],
        )

    def test_next_recommendation_uses_latest_reviewed_outcome_by_review_time(self):
        first_session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        second_session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )

        self.runtime.submit_answer(
            session_id=second_session["session_id"],
            transcript=_strong_transcript(),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(second_session["session_id"])
        self.runtime.submit_answer(
            session_id=first_session["session_id"],
            transcript=_weak_transcript(),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(first_session["session_id"])

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.82,
                            "confidence": 0.62,
                            "review_due_risk": 0.2,
                            "hint_dependency_signal": 0.0,
                            "last_evidence_at": "2026-03-20T10:00:00Z",
                        },
                    },
                    "subskill_state": {},
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.0,
                        "recent_abandonment_signal": 0.0,
                        "mock_readiness_estimate": 0.1,
                        "mock_readiness_confidence": 0.1,
                        "last_active_at": "2026-03-20T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-20T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Practice")
        self.assertEqual(decision["chosen_action"]["session_intent"], "Reinforce")

    def test_next_recommendation_uses_injected_projector_as_primary_state_input(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="Study",
            session_intent="LearnNew",
            unit_id=self.study_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=_strong_transcript(),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.28,
                            "confidence": 0.73,
                            "review_due_risk": 0.78,
                            "hint_dependency_signal": 0.05,
                            "last_evidence_at": "2026-03-20T11:00:00Z",
                        },
                    },
                    "subskill_state": {},
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.0,
                        "recent_abandonment_signal": 0.0,
                        "mock_readiness_estimate": 0.08,
                        "mock_readiness_confidence": 0.07,
                        "last_active_at": "2026-03-20T11:00:00Z",
                    },
                    "last_updated_at": "2026-03-20T11:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Practice")
        self.assertEqual(decision["chosen_action"]["session_intent"], "Remediate")
        self.assertIn("weak", decision["rationale"].lower())

    def test_next_recommendation_unlocks_mock_when_readiness_is_high_enough(self):
        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.82,
                            "confidence": 0.71,
                            "review_due_risk": 0.2,
                            "hint_dependency_signal": 0.05,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.76,
                            "confidence": 0.68,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                        "communication_clarity": {
                            "proficiency_estimate": 0.74,
                            "confidence": 0.67,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.05,
                        "recent_abandonment_signal": 0.1,
                        "mock_readiness_estimate": 0.32,
                        "mock_readiness_confidence": 0.21,
                        "last_active_at": "2026-03-21T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-21T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "MockInterview")
        self.assertEqual(decision["chosen_action"]["session_intent"], "ReadinessCheck")
        self.assertEqual(decision["chosen_action"]["target_type"], "scenario_family")
        self.assertEqual(decision["chosen_action"]["target_id"], "url_shortener")
        self.assertIn("readiness", decision["rationale"].lower())

    def test_next_recommendation_suppresses_mock_when_hint_dependency_is_too_high(self):
        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.82,
                            "confidence": 0.71,
                            "review_due_risk": 0.2,
                            "hint_dependency_signal": 0.24,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.76,
                            "confidence": 0.68,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.05,
                        "recent_abandonment_signal": 0.1,
                        "mock_readiness_estimate": 0.34,
                        "mock_readiness_confidence": 0.22,
                        "last_active_at": "2026-03-21T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-21T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertNotEqual(decision["chosen_action"]["mode"], "MockInterview")
        self.assertEqual(decision["chosen_action"]["session_intent"], "SpacedReview")

    def test_next_recommendation_avoids_immediate_repeat_after_reviewed_mock_attempt(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="MockInterview",
            session_intent="ReadinessCheck",
            unit_id=self.mock_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "I would begin with redirect reads, a durable mapping store, "
                "and id generation because the workload is read-heavy."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript=(
                "I would use a counter or random-id approach with collision checks "
                "and cache the redirect path."
            ),
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.82,
                            "confidence": 0.71,
                            "review_due_risk": 0.2,
                            "hint_dependency_signal": 0.05,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.76,
                            "confidence": 0.68,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                        "communication_clarity": {
                            "proficiency_estimate": 0.74,
                            "confidence": 0.67,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.05,
                        "recent_abandonment_signal": 0.1,
                        "mock_readiness_estimate": 0.34,
                        "mock_readiness_confidence": 0.24,
                        "last_active_at": "2026-03-21T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-21T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertNotEqual(decision["chosen_action"]["mode"], "MockInterview")
        self.assertIn("recent_mock_attempt", decision["blocking_signals"])

    def test_next_recommendation_does_not_unlock_bound_concepts_from_recent_mock_alone(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="MockInterview",
            session_intent="ReadinessCheck",
            unit_id=self.mock_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="I would use a database and maybe some caching.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Maybe a counter for ids and scale later if traffic grows.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {},
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.41,
                            "confidence": 0.58,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                        "communication_clarity": {
                            "proficiency_estimate": 0.52,
                            "confidence": 0.55,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.05,
                        "recent_abandonment_signal": 0.08,
                        "mock_readiness_estimate": 0.28,
                        "mock_readiness_confidence": 0.23,
                        "last_active_at": "2026-03-21T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-21T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Study")
        self.assertEqual(decision["chosen_action"]["session_intent"], "LearnNew")
        self.assertEqual(decision["chosen_action"]["target_id"], "concept.alpha-topic")
        self.assertIn("recent_mock_attempt", decision["blocking_signals"])
        self.assertFalse(
            any(
                action["target_id"].startswith("concept.url-shortener.")
                for action in decision["candidate_actions"]
                if action["target_type"] == "concept"
            )
        )

    def test_next_recommendation_uses_generic_weak_concept_follow_up_after_recent_mock(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="MockInterview",
            session_intent="ReadinessCheck",
            unit_id=self.mock_unit_id,
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="I would use a database and maybe some caching.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.submit_answer(
            session_id=session["session_id"],
            transcript="Maybe a counter for ids and scale later if traffic grows.",
            response_modality="text",
            submission_kind="manual_submit",
        )
        self.runtime.evaluate_pending_session(session["session_id"])

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.url-shortener.storage-choice": {
                            "proficiency_estimate": 0.33,
                            "confidence": 0.62,
                            "review_due_risk": 0.79,
                            "hint_dependency_signal": 0.08,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                        "concept.url-shortener.id-generation": {
                            "proficiency_estimate": 0.49,
                            "confidence": 0.43,
                            "review_due_risk": 0.58,
                            "hint_dependency_signal": 0.08,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.41,
                            "confidence": 0.58,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                        "communication_clarity": {
                            "proficiency_estimate": 0.52,
                            "confidence": 0.55,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.05,
                        "recent_abandonment_signal": 0.08,
                        "mock_readiness_estimate": 0.28,
                        "mock_readiness_confidence": 0.23,
                        "last_active_at": "2026-03-21T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-21T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertEqual(decision["chosen_action"]["mode"], "Practice")
        self.assertEqual(decision["chosen_action"]["session_intent"], "Remediate")
        self.assertEqual(
            decision["chosen_action"]["target_id"],
            "concept.url-shortener.storage-choice",
        )
        self.assertIn("recent_mock_attempt", decision["blocking_signals"])
        self.assertEqual(
            decision["supporting_signals"],
            [
                "weak_reviewed_outcome",
                "bounded_remediation_priority",
            ],
        )
        self.assertNotIn("post_mock_bound_concept_follow_up", decision["supporting_signals"])

    def test_next_recommendation_suppresses_mock_more_strongly_after_abandoned_mock(self):
        session = self.runtime.start_manual_session(
            user_id="demo-user",
            mode="MockInterview",
            session_intent="ReadinessCheck",
            unit_id=self.mock_unit_id,
        )
        self.runtime.abandon_session(session["session_id"], abandon_reason="explicit_exit")

        engine = RecommendationEngine(
            self.runtime,
            learner_projector=StubLearnerProjector(
                {
                    "user_id": "demo-user",
                    "concept_state": {
                        "concept.alpha-topic": {
                            "proficiency_estimate": 0.82,
                            "confidence": 0.71,
                            "review_due_risk": 0.2,
                            "hint_dependency_signal": 0.05,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "subskill_state": {
                        "tradeoff_reasoning": {
                            "proficiency_estimate": 0.76,
                            "confidence": 0.68,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                        "communication_clarity": {
                            "proficiency_estimate": 0.74,
                            "confidence": 0.67,
                            "last_evidence_at": "2026-03-21T10:00:00Z",
                        },
                    },
                    "trajectory_state": {
                        "recent_fatigue_signal": 0.05,
                        "recent_abandonment_signal": 0.18,
                        "mock_readiness_estimate": 0.34,
                        "mock_readiness_confidence": 0.24,
                        "last_active_at": "2026-03-21T10:00:00Z",
                    },
                    "last_updated_at": "2026-03-21T10:00:00Z",
                }
            ),
        )

        decision = engine.next_recommendation(user_id="demo-user")

        self.assertNotEqual(decision["chosen_action"]["mode"], "MockInterview")
        self.assertIn("recent_mock_abandonment", decision["blocking_signals"])


if __name__ == "__main__":
    unittest.main()


class StubLearnerProjector:
    def __init__(self, profile: dict):
        self._profile = copy.deepcopy(profile)

    def build_profile(self, runtime_reader, user_id: str) -> dict:
        profile = copy.deepcopy(self._profile)
        profile["user_id"] = user_id
        return profile
