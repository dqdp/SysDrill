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

        self.assertEqual(
            units,
            [
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
                }
            ],
        )

    def test_mock_materialization_skips_topics_without_scenarios(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["url-shortener"]["topic_package"]["canonical_content"]["scenarios"] = []

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

        self.assertEqual(units, [])

    def test_skips_topics_without_concepts(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["zeta-topic"]["topic_package"]["canonical_content"]["concepts"] = []

        units = materialize_executable_learning_units(
            catalog,
            mode="Study",
            session_intent="LearnNew",
        )

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["source_content_ids"], ["concept.alpha-topic"])


if __name__ == "__main__":
    unittest.main()
