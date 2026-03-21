import json
import tempfile
import unittest
from pathlib import Path

from system_design_space_importer.mapper import build_semantic_draft, run_map
from system_design_space_importer.models import parsed_source_fragment
from system_design_space_importer.paths import RunLayout


def _fragment(document_id, kind, order, text, heading_path=None):
    return parsed_source_fragment(
        fragment_id="frag.{0}.{1}.{2:03d}".format(document_id, kind, order),
        document_id=document_id,
        kind=kind,
        heading_path=heading_path or [],
        order=order,
        text=text,
        links=[],
        source_selector="test",
    )


class MapperTest(unittest.TestCase):
    def test_build_semantic_draft_uses_document_id_for_topic_slug(self):
        document_id = "hiring-goals"
        fragments = [
            _fragment(document_id, "title", 1, "Цель найма и подход к поиску кандидатов"),
            _fragment(document_id, "summary", 2, "Короткое summary"),
        ]

        draft = build_semantic_draft(document_id=document_id, fragments=fragments)

        self.assertEqual(draft["inferred_topic_slug"], document_id)
        self.assertEqual(
            draft["concepts"][0]["title"]["value"],
            "Цель найма и подход к поиску кандидатов",
        )

    def test_build_semantic_draft_extracts_usage_tradeoffs_and_distinct_why_signals(self):
        document_id = "caching"
        fragments = [
            _fragment(document_id, "title", 1, "Caching"),
            _fragment(document_id, "summary", 2, "Caching reduces load and latency."),
            _fragment(
                document_id,
                "section_body",
                3,
                "Use caching for read-heavy or latency-sensitive paths.",
            ),
            _fragment(
                document_id,
                "section_body",
                4,
                "The trade-offs are stale data, invalidation complexity, and extra memory cost.",
            ),
            _fragment(
                document_id,
                "section_body",
                5,
                "This matters because it protects the primary database during traffic spikes.",
            ),
        ]

        draft = build_semantic_draft(document_id=document_id, fragments=fragments)
        concept = draft["concepts"][0]

        self.assertEqual(
            concept["when_to_use"]["value"],
            ["Use caching for read-heavy or latency-sensitive paths."],
        )
        self.assertEqual(
            concept["tradeoffs"]["value"],
            ["The trade-offs are stale data, invalidation complexity, and extra memory cost."],
        )
        self.assertEqual(
            concept["why_it_matters"]["value"],
            ["This matters because it protects the primary database during traffic spikes."],
        )
        self.assertEqual(
            concept["when_to_use"]["provenance"][0]["fragment_ids"],
            ["frag.caching.section_body.003"],
        )
        self.assertEqual(
            concept["tradeoffs"]["provenance"][0]["fragment_ids"],
            ["frag.caching.section_body.004"],
        )
        self.assertEqual(
            concept["why_it_matters"]["provenance"][0]["fragment_ids"],
            ["frag.caching.section_body.005"],
        )

    def test_build_semantic_draft_does_not_copy_summary_into_why_it_matters_by_default(self):
        document_id = "generic-overview"
        fragments = [
            _fragment(document_id, "title", 1, "Generic Overview"),
            _fragment(
                document_id,
                "summary",
                2,
                "A generic descriptive summary without explicit why framing.",
            ),
        ]

        draft = build_semantic_draft(document_id=document_id, fragments=fragments)
        concept = draft["concepts"][0]

        self.assertEqual(concept["why_it_matters"]["value"], [])
        self.assertEqual(concept["when_to_use"]["value"], [])
        self.assertEqual(concept["tradeoffs"]["value"], [])

    def test_build_semantic_draft_seeds_one_scenario_for_explicit_incident_example_page(self):
        document_id = "troubleshooting-example"
        fragments = [
            _fragment(document_id, "title", 1, "Пример Troubleshooting Interview"),
            _fragment(
                document_id,
                "summary",
                2,
                (
                    "Публичное интервью: разбор архитектуры финтех-приложения, "
                    "инцидент со снижением платежей, диагностика в паре Lead + Junior."
                ),
                ["Пример Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "section_heading",
                3,
                "Легенда интервью",
                ["Пример Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "section_body",
                4,
                (
                    "По легенде кандидат работает как Lead в SRE-команде и "
                    "помогает Junior расследовать production-инцидент."
                ),
                ["Пример Troubleshooting Interview", "Легенда интервью"],
            ),
            _fragment(
                document_id,
                "section_heading",
                5,
                "Архитектура системы",
                ["Пример Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "section_body",
                6,
                (
                    "Перед стартом инцидента обсуждается архитектура "
                    "финтех-приложения Yellow и платёжного потока."
                ),
                ["Пример Troubleshooting Interview", "Архитектура системы"],
            ),
            _fragment(
                document_id,
                "section_heading",
                7,
                "Инцидент",
                ["Пример Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "section_body",
                8,
                (
                    "Junior сообщает о симптоме: алерт о снижении платежей, "
                    "после чего начинается совместная диагностика причины."
                ),
                ["Пример Troubleshooting Interview", "Инцидент"],
            ),
            _fragment(
                document_id,
                "bullet_list",
                9,
                "•Методология диагностики — системный подход vs хаотичный поиск",
                ["Пример Troubleshooting Interview", "Инцидент"],
            ),
            _fragment(
                document_id,
                "bullet_list",
                10,
                "•Формулирование гипотез и их проверка",
                ["Пример Troubleshooting Interview", "Инцидент"],
            ),
            _fragment(
                document_id,
                "bullet_list",
                11,
                "•Использование RED/USE методов для анализа",
                ["Пример Troubleshooting Interview", "Инцидент"],
            ),
            _fragment(
                document_id,
                "bullet_list",
                12,
                "•Коммуникация и направление менее опытного коллеги",
                ["Пример Troubleshooting Interview", "Инцидент"],
            ),
            _fragment(
                document_id,
                "bullet_list",
                13,
                "•Баланс между workaround и полноценным исправлением",
                ["Пример Troubleshooting Interview", "Инцидент"],
            ),
        ]

        draft = build_semantic_draft(document_id=document_id, fragments=fragments)

        self.assertEqual(len(draft["scenarios"]), 1)
        scenario = draft["scenarios"][0]
        self.assertEqual(scenario["id"]["value"], "scenario.troubleshooting-example")
        self.assertEqual(scenario["title"]["value"], "Пример Troubleshooting Interview")
        self.assertFalse(scenario["id"]["review_required"])
        self.assertFalse(scenario["title"]["review_required"])
        self.assertTrue(scenario["prompt"]["review_required"])
        self.assertTrue(scenario["content_difficulty_baseline"]["review_required"])
        self.assertTrue(scenario["expected_focus_areas"]["review_required"])
        self.assertTrue(scenario["canonical_axes"]["review_required"])
        self.assertTrue(scenario["canonical_follow_up_candidates"]["review_required"])
        self.assertIn("инцидент со снижением платежей", scenario["prompt"]["value"])
        self.assertIn("Lead", scenario["prompt"]["value"])
        self.assertEqual(scenario["content_difficulty_baseline"]["value"], "standard")
        self.assertIn(
            "Методология диагностики — системный подход vs хаотичный поиск",
            scenario["canonical_axes"]["value"],
        )
        self.assertIn(
            "Формулирование гипотез и их проверка",
            scenario["canonical_axes"]["value"],
        )
        self.assertTrue(
            any(
                "архитектура" in focus.lower()
                for focus in scenario["expected_focus_areas"]["value"]
            )
        )
        self.assertTrue(
            any(
                "платеж" in focus.lower() or "инцидент" in focus.lower()
                for focus in scenario["expected_focus_areas"]["value"]
            )
        )
        self.assertTrue(scenario["canonical_follow_up_candidates"]["value"])
        self.assertTrue(scenario["prompt"]["provenance"])
        self.assertTrue(scenario["canonical_axes"]["provenance"])
        self.assertEqual(
            scenario["canonical_axes"]["provenance"][0]["fragment_ids"],
            [
                "frag.troubleshooting-example.bullet_list.009",
                "frag.troubleshooting-example.bullet_list.010",
                "frag.troubleshooting-example.bullet_list.011",
                "frag.troubleshooting-example.bullet_list.012",
                "frag.troubleshooting-example.bullet_list.013",
            ],
        )
        self.assertNotIn("no scenario draft was emitted", draft["warnings"])
        self.assertNotIn("canonical axes were not inferred", draft["warnings"])

    def test_build_semantic_draft_does_not_seed_scenario_for_interview_theory_page(self):
        document_id = "troubleshooting-interview"
        fragments = [
            _fragment(document_id, "title", 1, "Troubleshooting Interview"),
            _fragment(
                document_id,
                "summary",
                2,
                (
                    "Формат SRE-интервью: диагностика инцидентов, критерии "
                    "оценки и сравнение с System Design."
                ),
                ["Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "section_heading",
                3,
                "Зачем нужно Troubleshooting Interview",
                ["Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "section_body",
                4,
                (
                    "Это формат интервью, который проверяет способность "
                    "кандидата диагностировать проблемы в production-системах."
                ),
                ["Troubleshooting Interview", "Зачем нужно Troubleshooting Interview"],
            ),
            _fragment(
                document_id,
                "bullet_list",
                5,
                "•Обратная связь о том, что стоит подтянуть",
                ["Troubleshooting Interview", "Зачем нужно Troubleshooting Interview"],
            ),
        ]

        draft = build_semantic_draft(document_id=document_id, fragments=fragments)

        self.assertEqual(draft["scenarios"], [])
        self.assertIn("no scenario draft was emitted", draft["warnings"])

    def test_run_map_preserves_distinct_document_ids_when_titles_collide(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            layout = RunLayout(out_dir=Path(temp_dir) / "out", run_id="map-collision")
            layout.ensure_base()

            fixtures = {
                "doc-one": [
                    _fragment("doc-one", "title", 1, "System Design Interview"),
                    _fragment("doc-one", "summary", 2, "Summary one"),
                ],
                "doc-two": [
                    _fragment("doc-two", "title", 1, "System Design Interview"),
                    _fragment("doc-two", "summary", 2, "Summary two"),
                ],
            }

            for document_id, fragments in fixtures.items():
                target = layout.fragments_dir / document_id / "fragments.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    json.dumps(fragments, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

            drafts = run_map(layout)

            self.assertEqual(sorted(drafts), ["doc-one", "doc-two"])
            self.assertTrue((layout.drafts_dir / "doc-one" / "semantic-draft.json").exists())
            self.assertTrue((layout.drafts_dir / "doc-two" / "semantic-draft.json").exists())


if __name__ == "__main__":
    unittest.main()
