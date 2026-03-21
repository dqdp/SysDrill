import copy
import unittest
from pathlib import Path

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.recommendation_engine import (
    NoRecommendationCandidatesError,
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
                {
                    "mode": "Practice",
                    "session_intent": "Reinforce",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "standard",
                    "strictness_profile": "standard",
                    "session_size": "single_unit",
                    "delivery_profile": "text_first",
                },
                {
                    "mode": "Practice",
                    "session_intent": "Remediate",
                    "target_type": "concept",
                    "target_id": "concept.alpha-topic",
                    "difficulty_profile": "targeted",
                    "strictness_profile": "standard",
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


if __name__ == "__main__":
    unittest.main()
