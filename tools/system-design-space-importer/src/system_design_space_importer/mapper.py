import re

from system_design_space_importer import __version__
from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.models import draft_field, provenance_ref
from system_design_space_importer.utils import strip_whitespace

_USAGE_CUES = (
    r"\buse\b",
    r"\bwhen\b",
    "read-heavy",
    "latency-sensitive",
    r"\bstateful\b",
    r"\bstateless\b",
    "workload",
    "нагруз",
    r"\bкогда\b",
    "подходит",
    "использ",
    "выбор",
    "примен",
)
_TRADEOFF_CUES = (
    r"\btrade-off\b",
    r"\btradeoffs\b",
    r"\btrade-offs\b",
    r"\btradeoff\b",
    "компромисс",
    r"\bcost\b",
    "complexity",
    "consistency",
    "eventual consistency",
    "stale",
    "replay",
    r"\brisk\b",
)
_WHY_CUES = (
    "matters because",
    "important because",
    "helps",
    "protects",
    "reduces",
    "improves",
    "allows",
    "enables",
    "помогает",
    "защищает",
    "снижает",
    "повышает",
    "важно",
    "позволяет",
)
_SCENARIO_EXAMPLE_CUES = (
    "example",
    "пример",
    "case",
    "кейс",
    "practical walkthrough",
)
_SCENARIO_INCIDENT_CUES = (
    "incident",
    "инцидент",
    "symptom",
    "симптом",
    "alert",
    "алерт",
)
_SCENARIO_STRONG_SYMPTOM_CUES = _SCENARIO_INCIDENT_CUES + (
    "error",
    "ошиб",
    "latency",
    "timeout",
    "снижени",
    "degrad",
)
_SCENARIO_SYMPTOM_CUES = _SCENARIO_STRONG_SYMPTOM_CUES + (
    "платеж",
    "payment",
)
_SCENARIO_LEGEND_CUES = (
    "legend",
    "легенда",
)
_SCENARIO_ARCHITECTURE_CUES = (
    "architecture",
    "архитектур",
    "flow",
    "поток",
    "system",
    "система",
)


def _first_fragment(fragments, kind):
    for fragment in fragments:
        if fragment["kind"] == kind:
            return fragment
    return None


def _fragments_by_kind(fragments, kind):
    return [fragment for fragment in fragments if fragment["kind"] == kind]


def _matches_any(text, cues):
    normalized = strip_whitespace(text).lower()
    return any(re.search(cue, normalized) for cue in cues)


def _content_window_fragments(fragments, max_fragments=24):
    title_index = 0
    for index, fragment in enumerate(fragments):
        if fragment["kind"] == "title":
            title_index = index
            break
    window = fragments[title_index + 1 : title_index + 1 + max_fragments]
    return [fragment for fragment in window if fragment["kind"] in {"summary", "section_body"}]


def _scenario_window_fragments(fragments, max_fragments=80):
    title_index = 0
    for index, fragment in enumerate(fragments):
        if fragment["kind"] == "title":
            title_index = index
            break
    window = fragments[title_index + 1 : title_index + 1 + max_fragments]
    allowed_kinds = {"summary", "section_heading", "section_body", "bullet_list"}
    return [fragment for fragment in window if fragment["kind"] in allowed_kinds]


def _field_provenance(document_id, matched_fragments, fallback_fragment):
    if matched_fragments:
        return [
            provenance_ref(
                document_id=document_id,
                fragment_ids=[fragment["fragment_id"] for fragment in matched_fragments],
                extraction_mode="rule",
                confidence=0.62,
                notes=["heuristic extraction requires editorial review"],
            )
        ]
    return [
        provenance_ref(
            document_id=document_id,
            fragment_ids=[fallback_fragment["fragment_id"]] if fallback_fragment else [],
            extraction_mode="llm_assisted",
            confidence=0.55,
            notes=["placeholder field requires editorial review"],
        )
    ]


def _scenario_field_provenance(document_id, matched_fragments, confidence=0.62):
    return [
        provenance_ref(
            document_id=document_id,
            fragment_ids=[fragment["fragment_id"] for fragment in matched_fragments],
            extraction_mode="rule",
            confidence=confidence,
            notes=["heuristic scenario seeding requires editorial review"],
        )
    ]


def _matched_fragment_texts(fragments, cues, exclude_kinds=()):
    matched_fragments = []
    values = []
    seen_values = set()
    for fragment in fragments:
        if fragment["kind"] in exclude_kinds:
            continue
        text = strip_whitespace(fragment["text"])
        if not text or not _matches_any(text, cues):
            continue
        if text in seen_values:
            continue
        matched_fragments.append(fragment)
        values.append(text)
        seen_values.add(text)
        if len(values) >= 3:
            break
    return values, matched_fragments


def _heading_path_matches(fragment, cues):
    return any(_matches_any(heading, cues) for heading in fragment.get("heading_path", []))


def _strip_list_prefix(text):
    return strip_whitespace(re.sub(r"^[\s•*-]+", "", text))


def _unique_fragment_texts(fragments, clean=False, limit=None):
    values = []
    seen = set()
    for fragment in fragments:
        text = _strip_list_prefix(fragment["text"]) if clean else strip_whitespace(fragment["text"])
        if not text or text in seen:
            continue
        values.append(text)
        seen.add(text)
        if limit is not None and len(values) >= limit:
            break
    return values


def _scenario_candidate_fragments(fragments, cues, kind=None):
    matched = []
    for fragment in fragments:
        if kind is not None and fragment["kind"] != kind:
            continue
        if _matches_any(fragment["text"], cues) or _heading_path_matches(fragment, cues):
            matched.append(fragment)
    return matched


def _build_scenarios(document_id, topic_slug, title_fragment, summary_fragment, fragments):
    if not title_fragment:
        return []

    title_text = strip_whitespace(title_fragment["text"])
    summary_text = strip_whitespace(summary_fragment["text"]) if summary_fragment else ""
    if not (
        _matches_any(title_text, _SCENARIO_EXAMPLE_CUES)
        or _matches_any(summary_text, _SCENARIO_EXAMPLE_CUES)
    ):
        return []

    scenario_fragments = _scenario_window_fragments(fragments)
    incident_bodies = [
        fragment
        for fragment in scenario_fragments
        if fragment["kind"] == "section_body"
        and _heading_path_matches(fragment, _SCENARIO_INCIDENT_CUES)
    ]
    incident_axes = [
        fragment
        for fragment in scenario_fragments
        if fragment["kind"] == "bullet_list"
        and _heading_path_matches(fragment, _SCENARIO_INCIDENT_CUES)
    ]
    if not incident_bodies or len(incident_axes) < 2:
        return []
    incident_prompt_bodies = [
        fragment
        for fragment in incident_bodies
        if _matches_any(fragment["text"], _SCENARIO_STRONG_SYMPTOM_CUES)
    ]
    if not incident_prompt_bodies:
        incident_prompt_bodies = [
            fragment
            for fragment in incident_bodies
            if _matches_any(fragment["text"], _SCENARIO_SYMPTOM_CUES)
        ]
    incident_prompt_fragment = (
        incident_prompt_bodies[0] if incident_prompt_bodies else incident_bodies[0]
    )

    legend_bodies = [
        fragment
        for fragment in scenario_fragments
        if fragment["kind"] == "section_body"
        and _heading_path_matches(fragment, _SCENARIO_LEGEND_CUES)
    ]
    architecture_bodies = [
        fragment
        for fragment in scenario_fragments
        if fragment["kind"] == "section_body"
        and _heading_path_matches(fragment, _SCENARIO_ARCHITECTURE_CUES)
    ]

    prompt_fragments = []
    for fragment in [summary_fragment]:
        if fragment is not None:
            prompt_fragments.append(fragment)
    if legend_bodies:
        prompt_fragments.append(legend_bodies[0])
    prompt_fragments.append(incident_prompt_fragment)

    expected_focus_fragments = []
    if architecture_bodies:
        expected_focus_fragments.append(architecture_bodies[0])
    expected_focus_fragments.append(incident_prompt_fragment)
    if summary_fragment is not None:
        expected_focus_fragments.append(summary_fragment)

    follow_up_fragments = []
    for fragment in scenario_fragments:
        if fragment["kind"] == "section_heading" and _matches_any(
            fragment["text"],
            ("архитектур", "architecture", "инцидент", "incident"),
        ):
            follow_up_fragments.append(fragment)
    follow_up_fragments.extend(incident_axes[:2])

    prompt_value = "\n\n".join(_unique_fragment_texts(prompt_fragments))
    expected_focus_values = _unique_fragment_texts(expected_focus_fragments, limit=3)
    canonical_axes_values = _unique_fragment_texts(incident_axes, clean=True, limit=5)
    follow_up_values = _unique_fragment_texts(follow_up_fragments, clean=True, limit=4)
    if not (prompt_value and expected_focus_values and canonical_axes_values and follow_up_values):
        return []

    title_provenance = provenance_ref(
        document_id=document_id,
        fragment_ids=[title_fragment["fragment_id"]],
        extraction_mode="rule",
        confidence=0.99,
    )
    return [
        {
            "id": draft_field(
                value="scenario.{0}".format(topic_slug),
                provenance=[title_provenance],
                review_required=False,
            ),
            "title": draft_field(
                value=title_text,
                provenance=[title_provenance],
                review_required=False,
            ),
            "prompt": draft_field(
                value=prompt_value,
                provenance=_scenario_field_provenance(document_id, prompt_fragments),
                review_required=True,
            ),
            "content_difficulty_baseline": draft_field(
                value="standard",
                provenance=_scenario_field_provenance(document_id, prompt_fragments),
                review_required=True,
            ),
            "expected_focus_areas": draft_field(
                value=expected_focus_values,
                provenance=_scenario_field_provenance(document_id, expected_focus_fragments),
                review_required=True,
            ),
            "canonical_axes": draft_field(
                value=canonical_axes_values,
                provenance=_scenario_field_provenance(document_id, incident_axes),
                review_required=True,
            ),
            "canonical_follow_up_candidates": draft_field(
                value=follow_up_values,
                provenance=_scenario_field_provenance(document_id, follow_up_fragments),
                review_required=True,
            ),
        }
    ]


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

    title_provenance = provenance_ref(
        document_id,
        [title_fragment["fragment_id"]] if title_fragment else [],
        "rule",
        0.99,
    )
    extraction_fragments = _content_window_fragments(fragments)
    why_values, why_fragments = _matched_fragment_texts(
        extraction_fragments,
        _WHY_CUES,
        exclude_kinds=("summary",),
    )
    when_to_use_values, when_to_use_fragments = _matched_fragment_texts(
        extraction_fragments,
        _USAGE_CUES,
    )
    tradeoff_values, tradeoff_fragments = _matched_fragment_texts(
        extraction_fragments,
        _TRADEOFF_CUES,
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
            value=why_values,
            provenance=_field_provenance(
                document_id=document_id,
                matched_fragments=why_fragments,
                fallback_fragment=description_fragment,
            ),
            review_required=True,
        ),
        "when_to_use": draft_field(
            value=when_to_use_values,
            provenance=_field_provenance(
                document_id=document_id,
                matched_fragments=when_to_use_fragments,
                fallback_fragment=description_fragment,
            ),
            review_required=True,
        ),
        "tradeoffs": draft_field(
            value=tradeoff_values,
            provenance=_field_provenance(
                document_id=document_id,
                matched_fragments=tradeoff_fragments,
                fallback_fragment=description_fragment,
            ),
            review_required=True,
        ),
        "related_concepts": draft_field(
            value=[],
            provenance=_field_provenance(
                document_id=document_id,
                matched_fragments=[],
                fallback_fragment=description_fragment,
            ),
            review_required=True,
        ),
        "prerequisites": draft_field(
            value=[],
            provenance=_field_provenance(
                document_id=document_id,
                matched_fragments=[],
                fallback_fragment=description_fragment,
            ),
            review_required=True,
        ),
    }

    scenarios = _build_scenarios(
        document_id=document_id,
        topic_slug=topic_slug,
        title_fragment=title_fragment,
        summary_fragment=summary_fragment,
        fragments=fragments,
    )
    warnings = []
    if not summary_fragment:
        warnings.append("summary fragment missing; description uses fallback")
    if not scenarios:
        warnings.append("canonical axes were not inferred")
        warnings.append("no scenario draft was emitted")

    return {
        "draft_id": "semdraft.{0}".format(topic_slug),
        "source_document_ids": [document_id],
        "inferred_topic_slug": topic_slug,
        "mapper_version": __version__,
        "concepts": [concept],
        "patterns": [],
        "scenarios": scenarios,
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
