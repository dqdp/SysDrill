import json
import tempfile
import unittest
from pathlib import Path

from system_design_space_importer.mapper import build_semantic_draft, run_map
from system_design_space_importer.models import parsed_source_fragment
from system_design_space_importer.paths import RunLayout


def _fragment(document_id, kind, order, text):
    return parsed_source_fragment(
        fragment_id="frag.{0}.{1}.{2:03d}".format(document_id, kind, order),
        document_id=document_id,
        kind=kind,
        heading_path=[],
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
