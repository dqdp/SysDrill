import copy
import unittest

from sysdrill_backend.rule_first_evaluator import (
    RuleFirstEvaluationError,
    evaluate_concept_recall,
    evaluate_rate_limiter_readiness,
    evaluate_url_shortener_readiness,
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
        self.url_shortener_request = {
            "session_id": "session.1001",
            "session_mode": "MockInterview",
            "session_intent": "ReadinessCheck",
            "executable_unit_id": (
                "elu.scenario_readiness_check.mock_interview.readiness_check."
                "scenario.url-shortener.basic"
            ),
            "unit_family": "scenario_readiness_check",
            "scenario_family": "url_shortener",
            "binding_id": "binding.url_shortener.v1",
            "transcript_text": (
                "The service is read-heavy and latency sensitive. I would run a "
                "redirect service with a key-value database mapping each short URL "
                "to the long URL. Reads can use caching and replicas, and the "
                "trade-off is more invalidation work."
            ),
            "follow_up_transcript_text": (
                "I would keep the read path fast with replicas and a key-value "
                "lookup, but I have not defended how links are minted yet."
            ),
            "hint_usage_summary": {
                "hint_count": 0,
                "used_prior_hints": False,
            },
            "answer_reveal_flag": False,
            "timing_summary": {
                "response_latency_ms": 62000,
            },
            "completion_status": "submitted",
            "strictness_profile": "strict",
        }
        self.rate_limiter_request = {
            "session_id": "session.2001",
            "session_mode": "MockInterview",
            "session_intent": "ReadinessCheck",
            "executable_unit_id": (
                "elu.scenario_readiness_check.mock_interview.readiness_check."
                "scenario.rate-limiter.basic"
            ),
            "unit_family": "scenario_readiness_check",
            "scenario_family": "rate_limiter",
            "binding_id": "binding.rate_limiter.v1",
            "transcript_text": (
                "I need tenant-aware request limits and I would likely use Redis-backed "
                "counters for coordination. I have not committed to one concrete rate-"
                "limiting algorithm yet."
            ),
            "follow_up_transcript_text": (
                "If Redis is temporarily unavailable I would fail closed briefly and "
                "return a bounded error response for strict fairness."
            ),
            "hint_usage_summary": {
                "hint_count": 0,
                "used_prior_hints": False,
            },
            "answer_reveal_flag": False,
            "timing_summary": {
                "response_latency_ms": 58000,
            },
            "completion_status": "submitted",
            "strictness_profile": "strict",
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

    def test_url_shortener_emits_negative_id_generation_signal_without_smearing(self):
        request = copy.deepcopy(self.url_shortener_request)
        request["bound_concept_ids"] = [
            "concept.url-shortener.id-generation",
            "concept.url-shortener.storage-choice",
            "concept.url-shortener.read-scaling",
            "concept.url-shortener.caching",
        ]

        result = evaluate_url_shortener_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertEqual(
            [
                signal["concept_id"]
                for signal in concept_signals
                if signal["direction"] == "negative"
            ],
            ["concept.url-shortener.id-generation"],
        )
        self.assertEqual(
            concept_signals[0]["evidence_basis"],
            ["expected_cue_missing"],
        )
        self.assertEqual(
            concept_signals[0]["source_criteria"],
            ["data_and_storage_choices"],
        )

    def test_url_shortener_concept_signals_respect_bound_concept_ids(self):
        request = copy.deepcopy(self.url_shortener_request)
        request["transcript_text"] = (
            "The service is read-heavy and latency sensitive. I would run a "
            "redirect service and use caching with replicas on the read path. "
            "The trade-off is more operational complexity."
        )
        request["follow_up_transcript_text"] = (
            "I would keep replicas for throughput and keep availability high."
        )
        request["bound_concept_ids"] = ["concept.url-shortener.storage-choice"]

        result = evaluate_url_shortener_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertEqual(
            [signal["concept_id"] for signal in concept_signals],
            ["concept.url-shortener.storage-choice"],
        )
        self.assertTrue(all(signal["direction"] == "negative" for signal in concept_signals))

    def test_url_shortener_does_not_emit_positive_concept_signal_from_vague_success(self):
        request = copy.deepcopy(self.url_shortener_request)
        request["follow_up_transcript_text"] = (
            "I would use a counter and collision checks, and I would keep the "
            "read path fast with replicas and a cache-backed lookup."
        )

        result = evaluate_url_shortener_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertFalse(any(signal["direction"] == "positive" for signal in concept_signals))

    def test_rate_limiter_emits_negative_algorithm_signal_without_smearing(self):
        request = copy.deepcopy(self.rate_limiter_request)
        request["bound_concept_ids"] = [
            "concept.rate-limiter.algorithm-choice",
            "concept.rate-limiter.state-placement",
            "concept.rate-limiter.failure-handling",
            "concept.rate-limiter.trade-offs",
        ]

        result = evaluate_rate_limiter_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertEqual(
            [
                signal["concept_id"]
                for signal in concept_signals
                if signal["direction"] == "negative"
            ],
            ["concept.rate-limiter.algorithm-choice"],
        )
        self.assertEqual(
            concept_signals[0]["source_criteria"],
            ["data_and_storage_choices"],
        )
        self.assertEqual(
            concept_signals[0]["evidence_basis"],
            ["expected_cue_missing"],
        )

    def test_rate_limiter_emits_negative_failure_handling_signal_without_smearing(self):
        request = copy.deepcopy(self.rate_limiter_request)
        request["transcript_text"] = (
            "I would use a token bucket with Redis counters shared across instances, "
            "and the trade-off is more cross-node coordination."
        )
        request["follow_up_transcript_text"] = (
            "I would keep Redis central for consistency, but I have not decided how to "
            "behave if Redis becomes stale or unavailable."
        )
        request["bound_concept_ids"] = [
            "concept.rate-limiter.algorithm-choice",
            "concept.rate-limiter.state-placement",
            "concept.rate-limiter.failure-handling",
            "concept.rate-limiter.trade-offs",
        ]

        result = evaluate_rate_limiter_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertEqual(
            [
                signal["concept_id"]
                for signal in concept_signals
                if signal["direction"] == "negative"
            ],
            ["concept.rate-limiter.failure-handling"],
        )

    def test_rate_limiter_concept_signals_respect_bound_concept_ids(self):
        request = copy.deepcopy(self.rate_limiter_request)
        request["transcript_text"] = (
            "I would use a token bucket with Redis-backed counters shared across nodes."
        )
        request["follow_up_transcript_text"] = (
            "I would centralize state for fairness, but I have not decided how to behave "
            "if Redis becomes stale or unavailable."
        )
        request["bound_concept_ids"] = ["concept.rate-limiter.failure-handling"]

        result = evaluate_rate_limiter_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertEqual(
            [signal["concept_id"] for signal in concept_signals],
            ["concept.rate-limiter.failure-handling"],
        )

    def test_rate_limiter_does_not_emit_concept_signal_from_generic_low_score_alone(self):
        request = copy.deepcopy(self.rate_limiter_request)
        request["transcript_text"] = "A rate limiter protects services from too many requests."
        request["follow_up_transcript_text"] = "It also needs some counters."
        request["bound_concept_ids"] = [
            "concept.rate-limiter.algorithm-choice",
            "concept.rate-limiter.state-placement",
            "concept.rate-limiter.failure-handling",
            "concept.rate-limiter.trade-offs",
        ]

        result = evaluate_rate_limiter_readiness(request)

        concept_signals = result["evaluation_result"]["downstream_signals"]["concept_mock_evidence"]
        self.assertEqual(concept_signals, [])


if __name__ == "__main__":
    unittest.main()
