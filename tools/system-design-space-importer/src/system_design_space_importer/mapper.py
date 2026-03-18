from system_design_space_importer import __version__
from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.models import draft_field, provenance_ref


def _first_fragment(fragments, kind):
    for fragment in fragments:
        if fragment["kind"] == kind:
            return fragment
    return None


def _fragments_by_kind(fragments, kind):
    return [fragment for fragment in fragments if fragment["kind"] == kind]


def build_semantic_draft(document_id, fragments):
    title_fragment = _first_fragment(fragments, "title")
    summary_fragment = _first_fragment(fragments, "summary")
    section_bodies = _fragments_by_kind(fragments, "section_body")
    title = title_fragment["text"] if title_fragment else document_id.replace("-", " ").title()
    # Exported topic slugs must remain stable across locales and title variants.
    # The source URL-derived document_id is the most deterministic identity we
    # have at importer stage, so we keep it as the canonical draft slug.
    topic_slug = document_id

    description_fragment = summary_fragment or (
        section_bodies[0] if section_bodies else title_fragment
    )
    description_text = description_fragment["text"] if description_fragment else title
    provenance = provenance_ref(
        document_id=document_id,
        fragment_ids=[description_fragment["fragment_id"]] if description_fragment else [],
        extraction_mode="rule",
        confidence=0.82 if summary_fragment else 0.55,
    )

    review_provenance = provenance_ref(
        document_id=document_id,
        fragment_ids=[description_fragment["fragment_id"]] if description_fragment else [],
        extraction_mode="llm_assisted",
        confidence=0.55,
        notes=["placeholder field requires editorial review"],
    )
    title_provenance = provenance_ref(
        document_id,
        [title_fragment["fragment_id"]] if title_fragment else [],
        "rule",
        0.99,
    )

    concept = {
        "id": draft_field(
            value="concept.{0}".format(topic_slug),
            provenance=[title_provenance],
            review_required=False,
        ),
        "title": draft_field(
            value=title,
            provenance=[title_provenance],
            review_required=False,
        ),
        "description": draft_field(
            value=description_text,
            provenance=[provenance],
            review_required=False if summary_fragment else True,
        ),
        "why_it_matters": draft_field(
            value=[description_text],
            provenance=[review_provenance],
            review_required=True,
        ),
        "when_to_use": draft_field(
            value=[],
            provenance=[review_provenance],
            review_required=True,
        ),
        "tradeoffs": draft_field(
            value=[],
            provenance=[review_provenance],
            review_required=True,
        ),
        "related_concepts": draft_field(
            value=[],
            provenance=[review_provenance],
            review_required=True,
        ),
        "prerequisites": draft_field(
            value=[],
            provenance=[review_provenance],
            review_required=True,
        ),
    }

    warnings = []
    if not summary_fragment:
        warnings.append("summary fragment missing; description uses fallback")
    warnings.append("canonical axes were not inferred")
    warnings.append("no scenario draft was emitted")

    return {
        "draft_id": "semdraft.{0}".format(topic_slug),
        "source_document_ids": [document_id],
        "inferred_topic_slug": topic_slug,
        "mapper_version": __version__,
        "concepts": [concept],
        "patterns": [],
        "scenarios": [],
        "hint_ladders": [],
        "unresolved_fragment_ids": [],
        "warnings": warnings,
    }


def run_map(layout):
    layout.ensure_base()
    drafts = {}
    for fragments_path in layout.fragments_dir.glob("*/fragments.json"):
        document_id = fragments_path.parent.name
        fragments = read_json(fragments_path)
        draft = build_semantic_draft(document_id=document_id, fragments=fragments)
        output_path = layout.drafts_dir / draft["inferred_topic_slug"] / "semantic-draft.json"
        write_json(output_path, draft)
        drafts[draft["inferred_topic_slug"]] = draft
    return drafts
