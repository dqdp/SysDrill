import unittest

from system_design_space_importer.models import draft_field, provenance_ref
from system_design_space_importer.validator import validate_semantic_draft


def _provenance(document_id="troubleshooting-example", fragment_ids=None, confidence=0.62):
    return [
        provenance_ref(
            document_id=document_id,
            fragment_ids=fragment_ids or ["frag.{0}.summary.001".format(document_id)],
            extraction_mode="rule",
            confidence=confidence,
            notes=["heuristic extraction requires editorial review"],
        )
    ]


def _minimal_concept():
    return {
        "id": draft_field("concept.example", _provenance(confidence=0.99), False),
        "title": draft_field("Example", _provenance(confidence=0.99), False),
        "description": draft_field("Example description", _provenance(confidence=0.82), False),
        "why_it_matters": draft_field(["Why it matters"], _provenance(), True),
        "when_to_use": draft_field(["When to use it"], _provenance(), True),
        "tradeoffs": draft_field(["Trade-off"], _provenance(), True),
        "related_concepts": draft_field([], _provenance(), True),
        "prerequisites": draft_field([], _provenance(), True),
    }


def _valid_scenario():
    return {
        "id": draft_field(
            "scenario.troubleshooting-example",
            _provenance(fragment_ids=["frag.troubleshooting-example.title.001"], confidence=0.99),
            False,
        ),
        "title": draft_field(
            "Пример Troubleshooting Interview",
            _provenance(fragment_ids=["frag.troubleshooting-example.title.001"], confidence=0.99),
            False,
        ),
        "prompt": draft_field(
            "Разберите incident со снижением платежей и опишите ход диагностики.",
            _provenance(
                fragment_ids=[
                    "frag.troubleshooting-example.summary.001",
                    "frag.troubleshooting-example.section_body.048",
                    "frag.troubleshooting-example.section_body.066",
                ]
            ),
            True,
        ),
        "content_difficulty_baseline": draft_field("standard", _provenance(), True),
        "expected_focus_areas": draft_field(
            ["Архитектура платёжного потока", "Диагностика инцидента"],
            _provenance(),
            True,
        ),
        "canonical_axes": draft_field(
            [
                "Методология диагностики — системный подход vs хаотичный поиск",
                "Формулирование гипотез и их проверка",
            ],
            _provenance(),
            True,
        ),
        "canonical_follow_up_candidates": draft_field(
            [
                "Уточнить архитектурный контекст платёжного потока",
                "Разобрать workaround и полноценное исправление",
            ],
            _provenance(),
            True,
        ),
    }


class ValidatorTest(unittest.TestCase):
    def test_validate_semantic_draft_rejects_scenario_missing_required_field(self):
        draft = {
            "draft_id": "semdraft.troubleshooting-example",
            "source_document_ids": ["troubleshooting-example"],
            "inferred_topic_slug": "troubleshooting-example",
            "mapper_version": "0.1.0",
            "concepts": [_minimal_concept()],
            "patterns": [],
            "scenarios": [
                {key: value for key, value in _valid_scenario().items() if key != "canonical_axes"}
            ],
            "hint_ladders": [],
            "warnings": [],
        }

        report = validate_semantic_draft(draft)

        self.assertFalse(report["schema_valid"])
        self.assertIn("scenarios[0].canonical_axes", report["missing_required_paths"])

    def test_validate_semantic_draft_rejects_scenario_with_empty_required_list(self):
        scenario = _valid_scenario()
        scenario["canonical_follow_up_candidates"] = draft_field([], _provenance(), True)
        draft = {
            "draft_id": "semdraft.troubleshooting-example",
            "source_document_ids": ["troubleshooting-example"],
            "inferred_topic_slug": "troubleshooting-example",
            "mapper_version": "0.1.0",
            "concepts": [_minimal_concept()],
            "patterns": [],
            "scenarios": [scenario],
            "hint_ladders": [],
            "warnings": [],
        }

        report = validate_semantic_draft(draft)

        self.assertFalse(report["schema_valid"])
        self.assertIn(
            "scenarios[0].canonical_follow_up_candidates",
            report["missing_required_paths"],
        )

    def test_validate_semantic_draft_accepts_valid_seeded_scenario(self):
        draft = {
            "draft_id": "semdraft.troubleshooting-example",
            "source_document_ids": ["troubleshooting-example"],
            "inferred_topic_slug": "troubleshooting-example",
            "mapper_version": "0.1.0",
            "concepts": [_minimal_concept()],
            "patterns": [],
            "scenarios": [_valid_scenario()],
            "hint_ladders": [],
            "warnings": [],
        }

        report = validate_semantic_draft(draft)

        self.assertTrue(report["schema_valid"])
        self.assertEqual(report["missing_required_paths"], [])


if __name__ == "__main__":
    unittest.main()
