import copy
import unittest
from pathlib import Path

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.executable_learning_unit_materializer import (
    ExecutableLearningUnitMaterializationError,
    materialize_executable_learning_units,
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

    def test_rejects_unsupported_mode_intent_combination(self):
        with self.assertRaisesRegex(ExecutableLearningUnitMaterializationError, "unsupported"):
            materialize_executable_learning_units(
                self.catalog,
                mode="Practice",
                session_intent="LearnNew",
            )

    def test_rejects_mock_interview_for_concept_recall_units(self):
        with self.assertRaisesRegex(ExecutableLearningUnitMaterializationError, "MockInterview"):
            materialize_executable_learning_units(
                self.catalog,
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
