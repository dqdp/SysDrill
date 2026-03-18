import copy
import unittest

from sysdrill_backend.rule_first_evaluator import (
    RuleFirstEvaluationError,
    evaluate_concept_recall,
)


class RuleFirstEvaluatorTest(unittest.TestCase):
    def setUp(self):
        self.base_request = {
            "session_id": "session.0001",
            "session_mode": "Study",
            "session_intent": "LearnNew",
            "executable_unit_id": "elu.concept_recall.study.learn_new.concept.alpha-topic",
            "unit_family": "concept_recall",
            "binding_id": "binding.concept_recall.v1",
            "transcript_text": (
                "Caching is storing frequently accessed data in a faster layer to reduce "
                "latency and backend load. Use it for read-heavy or latency-sensitive "
                "paths. The trade-offs are stale data, invalidation complexity, and "
                "extra memory cost."
            ),
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
        }

    def test_empty_transcript_yields_low_confidence_and_missing_dimensions(self):
        request = copy.deepcopy(self.base_request)
        request["transcript_text"] = ""

        result = evaluate_concept_recall(request)

        self.assertLess(result["evaluation_result"]["overall_confidence"], 0.5)
        self.assertEqual(
            result["evaluation_result"]["missing_dimensions"],
            ["concept_explanation", "usage_judgment", "trade_off_articulation"],
        )
        self.assertTrue(
            all(
                criterion["score_band"] in {0, 1}
                for criterion in result["evaluation_result"]["criterion_results"]
            )
        )

    def test_full_answer_scores_higher_than_definition_only_answer(self):
        definition_only = copy.deepcopy(self.base_request)
        definition_only["transcript_text"] = (
            "Caching is storing data in a faster layer to reduce latency."
        )

        definition_result = evaluate_concept_recall(definition_only)
        full_result = evaluate_concept_recall(self.base_request)

        self.assertLess(
            definition_result["evaluation_result"]["weighted_score"],
            full_result["evaluation_result"]["weighted_score"],
        )
        self.assertIn(
            "usage_judgment",
            definition_result["evaluation_result"]["missing_dimensions"],
        )
        self.assertIn(
            "trade_off_articulation",
            definition_result["evaluation_result"]["missing_dimensions"],
        )

    def test_practice_mode_is_stricter_than_study_for_same_transcript(self):
        practice_request = copy.deepcopy(self.base_request)
        practice_request["session_mode"] = "Practice"
        practice_request["session_intent"] = "Remediate"
        practice_request["strictness_profile"] = "standard"

        study_result = evaluate_concept_recall(self.base_request)
        practice_result = evaluate_concept_recall(practice_request)

        self.assertLess(
            practice_result["evaluation_result"]["weighted_score"],
            study_result["evaluation_result"]["weighted_score"],
        )

    def test_support_usage_reduces_confidence_and_increases_dependency_signal(self):
        supported_request = copy.deepcopy(self.base_request)
        supported_request["hint_usage_summary"] = {
            "hint_count": 1,
            "used_prior_hints": True,
        }
        supported_request["answer_reveal_flag"] = True

        independent_result = evaluate_concept_recall(self.base_request)
        supported_result = evaluate_concept_recall(supported_request)

        self.assertLess(
            supported_result["evaluation_result"]["overall_confidence"],
            independent_result["evaluation_result"]["overall_confidence"],
        )
        self.assertGreater(
            supported_result["evaluation_result"]["downstream_signals"]["hint_dependency"],
            independent_result["evaluation_result"]["downstream_signals"]["hint_dependency"],
        )

    def test_evaluator_output_is_deterministic(self):
        first_result = evaluate_concept_recall(copy.deepcopy(self.base_request))
        second_result = evaluate_concept_recall(copy.deepcopy(self.base_request))

        self.assertEqual(first_result, second_result)

    def test_rejects_unsupported_binding_or_unit_family(self):
        request = copy.deepcopy(self.base_request)
        request["binding_id"] = "binding.unsupported"

        with self.assertRaisesRegex(RuleFirstEvaluationError, "binding"):
            evaluate_concept_recall(request)


if __name__ == "__main__":
    unittest.main()
