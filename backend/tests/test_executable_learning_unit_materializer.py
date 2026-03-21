import copy
import unittest
from pathlib import Path

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.executable_learning_unit_materializer import (
    ExecutableLearningUnitMaterializationError,
    materialize_executable_learning_units,
    supported_materialization_pairs,
)


class ExecutableLearningUnitMaterializerTest(unittest.TestCase):
    def setUp(self):
        self.export_root = Path(__file__).parent / "fixtures" / "export_root"
        self.catalog = load_topic_catalog(self.export_root, allow_draft_bundles=True)

    def test_materializes_deterministically_ordered_concept_recall_units_for_study(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["zeta-topic"]["topic_package"]["learning_design_drafts"] = {
            "candidate_card_types": ["recall"],
        }

        units = materialize_executable_learning_units(
            catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(
            [unit["id"] for unit in units],
            [
                "elu.concept_recall.study.learn_new.concept.alpha-topic",
                "elu.concept_recall.study.learn_new.concept.rate-limiter.algorithm-choice",
                "elu.concept_recall.study.learn_new.concept.rate-limiter.failure-handling",
                "elu.concept_recall.study.learn_new.concept.rate-limiter.state-placement",
                "elu.concept_recall.study.learn_new.concept.rate-limiter.trade-offs",
                "elu.concept_recall.study.learn_new.concept.url-shortener.caching",
                "elu.concept_recall.study.learn_new.concept.url-shortener.id-generation",
                "elu.concept_recall.study.learn_new.concept.url-shortener.read-scaling",
                "elu.concept_recall.study.learn_new.concept.url-shortener.storage-choice",
                "elu.concept_recall.study.learn_new.concept.zeta-topic",
            ],
        )
        self.assertEqual(
            units[0],
            {
                "id": "elu.concept_recall.study.learn_new.concept.alpha-topic",
                "source_content_ids": ["concept.alpha-topic"],
                "mode": "Study",
                "session_intent": "LearnNew",
                "visible_prompt": (
                    "Explain the concept 'Кэширование'. Cover what it is, "
                    "when to use it, and the main trade-offs."
                ),
                "pedagogical_goal": "independent_concept_recall",
                "effective_difficulty": "introductory",
                "allowed_hint_levels": [1, 2, 3],
                "follow_up_envelope": {
                    "max_follow_ups": 0,
                    "follow_up_style": "none",
                },
                "completion_rules": {
                    "submission_kind": "manual_submit",
                    "answer_boundary": "single_response",
                    "allows_answer_reveal": True,
                },
                "evaluation_binding_id": "binding.concept_recall.v1",
            },
        )

    def test_materialization_is_stable_and_does_not_mutate_catalog(self):
        original_catalog = copy.deepcopy(self.catalog)

        first_units = materialize_executable_learning_units(
            self.catalog,
            mode="Study",
            session_intent="LearnNew",
        )
        second_units = materialize_executable_learning_units(
            self.catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(first_units, second_units)
        self.assertEqual(self.catalog, original_catalog)

    def test_materializes_mode_aware_policy_for_practice_remediation(self):
        units = materialize_executable_learning_units(
            self.catalog,
            mode="Practice",
            session_intent="Remediate",
        )

        self.assertEqual(units[0]["effective_difficulty"], "targeted")
        self.assertEqual(units[0]["allowed_hint_levels"], [1, 2])
        self.assertEqual(
            units[0]["follow_up_envelope"],
            {
                "max_follow_ups": 1,
                "follow_up_style": "bounded_probe",
            },
        )
        self.assertEqual(
            units[0]["completion_rules"],
            {
                "submission_kind": "manual_submit",
                "answer_boundary": "single_response",
                "allows_answer_reveal": False,
            },
        )

    def test_practice_prompt_uses_richer_applied_framing_when_context_is_available(self):
        study_units = materialize_executable_learning_units(
            self.catalog,
            mode="Study",
            session_intent="LearnNew",
        )
        practice_units = materialize_executable_learning_units(
            self.catalog,
            mode="Practice",
            session_intent="Remediate",
        )

        self.assertEqual(
            study_units[0]["visible_prompt"],
            (
                "Explain the concept 'Кэширование'. Cover what it is, when to use it, "
                "and the main trade-offs."
            ),
        )
        self.assertEqual(
            practice_units[0]["visible_prompt"],
            (
                "You're advising a teammate on whether to use 'Кэширование' in a real "
                "system discussion. Context: Кэш снижает нагрузку и латентность. Why it "
                "matters: Снижает нагрузку на базу данных. Explain what it is, when you "
                "would use it, and the main trade-offs you would call out."
            ),
        )

    def test_practice_prompt_falls_back_cleanly_when_optional_context_is_empty(self):
        catalog = copy.deepcopy(self.catalog)
        concept = catalog["alpha-topic"]["topic_package"]["canonical_content"]["concepts"][0]
        concept["description"]["value"] = ""
        concept["why_it_matters"]["value"] = []

        units = materialize_executable_learning_units(
            catalog,
            mode="Practice",
            session_intent="Reinforce",
        )

        self.assertEqual(
            units[0]["visible_prompt"],
            (
                "You're advising a teammate on whether to use 'Кэширование' in a real "
                "system discussion. Explain what it is, when you would use it, and the "
                "main trade-offs you would call out."
            ),
        )

    def test_rejects_unsupported_mode_intent_combination(self):
        with self.assertRaisesRegex(ExecutableLearningUnitMaterializationError, "unsupported"):
            materialize_executable_learning_units(
                self.catalog,
                mode="Practice",
                session_intent="LearnNew",
            )

    def test_supported_materialization_pairs_adds_one_mock_readiness_pair(self):
        self.assertEqual(
            supported_materialization_pairs(),
            [
                ("MockInterview", "ReadinessCheck"),
                ("Practice", "Reinforce"),
                ("Practice", "Remediate"),
                ("Study", "LearnNew"),
                ("Study", "Reinforce"),
                ("Study", "SpacedReview"),
            ],
        )

    def test_materializes_seeded_mock_readiness_unit_for_url_shortener(self):
        units = materialize_executable_learning_units(
            self.catalog,
            mode="MockInterview",
            session_intent="ReadinessCheck",
        )

        self.assertEqual(len(units), 2)
        self.assertIn(
            {
                "id": (
                    "elu.scenario_readiness_check.mock_interview.readiness_check."
                    "scenario.url-shortener.basic"
                ),
                "source_content_ids": ["scenario.url-shortener.basic"],
                "mode": "MockInterview",
                "session_intent": "ReadinessCheck",
                "unit_family": "scenario_readiness_check",
                "scenario_family": "url_shortener",
                "scenario_title": "Design a URL Shortener",
                "visible_prompt": (
                    "Design a URL Shortener for a read-heavy product with high "
                    "availability requirements."
                ),
                "bound_concept_ids": [
                    "concept.url-shortener.id-generation",
                    "concept.url-shortener.storage-choice",
                    "concept.url-shortener.read-scaling",
                    "concept.url-shortener.caching",
                ],
                "canonical_follow_up_candidates": [
                    (
                        "How would you generate short identifiers without creating "
                        "avoidable collisions?"
                    ),
                    "What would change if write traffic grew much faster than expected?",
                    "Where would caching help, and where could it create correctness risk?",
                ],
                "pedagogical_goal": "bounded_mock_readiness_check",
                "effective_difficulty": "standard",
                "allowed_hint_levels": [1],
                "follow_up_envelope": {
                    "max_follow_ups": 1,
                    "follow_up_style": "bounded_probe",
                },
                "completion_rules": {
                    "submission_kind": "manual_submit",
                    "answer_boundary": "bounded_follow_up",
                    "allows_answer_reveal": False,
                },
                "evaluation_binding_id": "binding.url_shortener.v1",
            },
            units,
        )

    def test_materializes_seeded_mock_readiness_unit_for_rate_limiter(self):
        units = materialize_executable_learning_units(
            self.catalog,
            mode="MockInterview",
            session_intent="ReadinessCheck",
        )

        self.assertIn(
            {
                "id": (
                    "elu.scenario_readiness_check.mock_interview.readiness_check."
                    "scenario.rate-limiter.basic"
                ),
                "source_content_ids": ["scenario.rate-limiter.basic"],
                "mode": "MockInterview",
                "session_intent": "ReadinessCheck",
                "unit_family": "scenario_readiness_check",
                "scenario_family": "rate_limiter",
                "scenario_title": "Design a Rate Limiter",
                "visible_prompt": (
                    "Design a Rate Limiter for a multi-tenant API where strict fairness "
                    "matters more than occasional burst throughput."
                ),
                "bound_concept_ids": [
                    "concept.rate-limiter.algorithm-choice",
                    "concept.rate-limiter.state-placement",
                    "concept.rate-limiter.failure-handling",
                    "concept.rate-limiter.trade-offs",
                ],
                "canonical_follow_up_candidates": [
                    "Which rate-limiting algorithm would you choose, and why?",
                    "Where would you keep limiter state if the API is deployed across regions?",
                    (
                        "What should happen if the limiter state store becomes stale or "
                        "temporarily unavailable?"
                    ),
                ],
                "pedagogical_goal": "bounded_mock_readiness_check",
                "effective_difficulty": "standard",
                "allowed_hint_levels": [1],
                "follow_up_envelope": {
                    "max_follow_ups": 1,
                    "follow_up_style": "bounded_probe",
                },
                "completion_rules": {
                    "submission_kind": "manual_submit",
                    "answer_boundary": "bounded_follow_up",
                    "allows_answer_reveal": False,
                },
                "evaluation_binding_id": "binding.rate_limiter.v1",
            },
            units,
        )

    def test_materializes_seeded_url_shortener_concept_recall_units_for_study(self):
        units = materialize_executable_learning_units(
            self.catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(
            [
                unit["source_content_ids"][0]
                for unit in units
                if unit["source_content_ids"][0].startswith("concept.url-shortener.")
            ],
            [
                "concept.url-shortener.caching",
                "concept.url-shortener.id-generation",
                "concept.url-shortener.read-scaling",
                "concept.url-shortener.storage-choice",
            ],
        )

    def test_materializes_seeded_rate_limiter_concept_recall_units_for_study(self):
        units = materialize_executable_learning_units(
            self.catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(
            [
                unit["source_content_ids"][0]
                for unit in units
                if unit["source_content_ids"][0].startswith("concept.rate-limiter.")
            ],
            [
                "concept.rate-limiter.algorithm-choice",
                "concept.rate-limiter.failure-handling",
                "concept.rate-limiter.state-placement",
                "concept.rate-limiter.trade-offs",
            ],
        )

    def test_mock_materialization_skips_topics_without_scenarios(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["url-shortener"]["topic_package"]["canonical_content"]["scenarios"] = []
        catalog["rate-limiter"]["topic_package"]["canonical_content"]["scenarios"] = []

        units = materialize_executable_learning_units(
            catalog,
            mode="MockInterview",
            session_intent="ReadinessCheck",
        )

        self.assertEqual(units, [])

    def test_mock_materialization_skips_topics_without_mini_scenario_candidate_type(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["url-shortener"]["topic_package"]["learning_design_drafts"][
            "candidate_card_types"
        ] = ["recall"]
        catalog["rate-limiter"]["topic_package"]["learning_design_drafts"][
            "candidate_card_types"
        ] = ["recall"]

        units = materialize_executable_learning_units(
            catalog,
            mode="MockInterview",
            session_intent="ReadinessCheck",
        )

        self.assertEqual(units, [])

    def test_mock_materialization_fails_closed_for_malformed_scenario_record(self):
        catalog = copy.deepcopy(self.catalog)
        del catalog["url-shortener"]["topic_package"]["canonical_content"]["scenarios"][0]["prompt"]

        with self.assertRaisesRegex(
            ExecutableLearningUnitMaterializationError,
            "scenario field 'prompt'",
        ):
            materialize_executable_learning_units(
                catalog,
                mode="MockInterview",
                session_intent="ReadinessCheck",
            )

    def test_mock_materialization_fails_closed_for_unknown_bound_concept_id(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["url-shortener"]["topic_package"]["canonical_content"]["scenarios"][0][
            "bound_concept_ids"
        ] = ["concept.missing"]

        with self.assertRaisesRegex(
            ExecutableLearningUnitMaterializationError,
            "unknown concept id",
        ):
            materialize_executable_learning_units(
                catalog,
                mode="MockInterview",
                session_intent="ReadinessCheck",
            )

    def test_mock_materialization_tolerates_missing_bound_concept_ids(self):
        catalog = copy.deepcopy(self.catalog)
        del catalog["url-shortener"]["topic_package"]["canonical_content"]["scenarios"][0][
            "bound_concept_ids"
        ]

        units = materialize_executable_learning_units(
            catalog,
            mode="MockInterview",
            session_intent="ReadinessCheck",
        )

        url_shortener_units = [
            unit for unit in units if unit["source_content_ids"] == ["scenario.url-shortener.basic"]
        ]
        self.assertEqual(len(url_shortener_units), 1)
        self.assertNotIn("bound_concept_ids", url_shortener_units[0])

    def test_skips_topics_without_recall_candidate_type(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["alpha-topic"]["topic_package"]["learning_design_drafts"][
            "candidate_card_types"
        ] = []

        units = materialize_executable_learning_units(
            catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertFalse(
            any(unit["source_content_ids"] == ["concept.alpha-topic"] for unit in units)
        )
        self.assertEqual(
            [unit["source_content_ids"][0] for unit in units],
            [
                "concept.rate-limiter.algorithm-choice",
                "concept.rate-limiter.failure-handling",
                "concept.rate-limiter.state-placement",
                "concept.rate-limiter.trade-offs",
                "concept.url-shortener.caching",
                "concept.url-shortener.id-generation",
                "concept.url-shortener.read-scaling",
                "concept.url-shortener.storage-choice",
            ],
        )

    def test_skips_topics_without_concepts(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["zeta-topic"]["topic_package"]["canonical_content"]["concepts"] = []

        units = materialize_executable_learning_units(
            catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(
            [unit["source_content_ids"][0] for unit in units],
            [
                "concept.alpha-topic",
                "concept.rate-limiter.algorithm-choice",
                "concept.rate-limiter.failure-handling",
                "concept.rate-limiter.state-placement",
                "concept.rate-limiter.trade-offs",
                "concept.url-shortener.caching",
                "concept.url-shortener.id-generation",
                "concept.url-shortener.read-scaling",
                "concept.url-shortener.storage-choice",
            ],
        )


if __name__ == "__main__":
    unittest.main()
