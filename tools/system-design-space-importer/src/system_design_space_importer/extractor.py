import re
from html import unescape
from html.parser import HTMLParser

from system_design_space_importer.jsonio import write_json
from system_design_space_importer.models import parsed_source_fragment
from system_design_space_importer.utils import strip_whitespace


def _extract_html_block(html):
    for tag in ("main", "article", "body"):
        match = re.search(
            r"<{0}\b[^>]*>(.*?)</{0}>".format(tag),
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1)
    return html


class FragmentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.heading_path = []
        self.current_tag = None
        self.current_text = []
        self.current_links = []
        self.current_href = None
        self.current_anchor_text = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag in ("h1", "h2", "h3", "p", "li"):
            self.current_tag = tag
            self.current_text = []
            self.current_links = []
        elif tag == "a":
            self.current_href = attrs_dict.get("href")
            self.current_anchor_text = []

    def handle_data(self, data):
        if self.current_tag is not None:
            self.current_text.append(data)
        if self.current_href is not None:
            self.current_anchor_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href is not None:
            link_title = strip_whitespace(unescape("".join(self.current_anchor_text)))
            link_payload = {"url": self.current_href}
            if link_title:
                link_payload["title"] = link_title
            if self.current_tag is not None:
                self.current_links.append(link_payload)
            elif link_title:
                self.blocks.append(
                    {
                        "tag": "a",
                        "kind": "reference_link",
                        "heading_path": list(self.heading_path),
                        "text": link_title,
                        "links": [link_payload],
                    }
                )
            self.current_href = None
            self.current_anchor_text = []
            return

        if tag != self.current_tag:
            return

        text = strip_whitespace(unescape("".join(self.current_text)))
        if not text:
            self.current_tag = None
            self.current_text = []
            self.current_links = []
            return

        kind = "section_body"
        heading_path = list(self.heading_path)
        if tag == "h1":
            kind = "title"
            self.heading_path = [text]
            heading_path = []
        elif tag == "h2":
            kind = "section_heading"
            root = self.heading_path[:1]
            self.heading_path = root + [text]
            heading_path = root
        elif tag == "h3":
            kind = "section_heading"
            root = self.heading_path[:2]
            self.heading_path = root + [text]
            heading_path = root
        elif tag == "li":
            kind = "bullet_list"
            heading_path = list(self.heading_path)

        self.blocks.append(
            {
                "tag": tag,
                "kind": kind,
                "heading_path": heading_path,
                "text": text,
                "links": list(self.current_links),
            }
        )

        self.current_tag = None
        self.current_text = []
        self.current_links = []


def parse_fragments(html):
    parser = FragmentParser()
    parser.feed(_extract_html_block(html))
    blocks = parser.blocks

    seen_title = False
    seen_summary = False
    counters = {}
    fragments = []
    for order, block in enumerate(blocks, start=1):
        kind = block["kind"]
        if kind == "title":
            seen_title = True
        elif kind == "section_body" and seen_title and not seen_summary:
            kind = "summary"
            seen_summary = True

        counters[kind] = counters.get(kind, 0) + 1
        fragment_id = "frag.{0}.{1}.{2:03d}".format(
            "document",
            kind,
            counters[kind],
        )
        fragments.append(
            parsed_source_fragment(
                fragment_id=fragment_id,
                document_id="",
                kind=kind,
                heading_path=block["heading_path"],
                order=order,
                text=block["text"],
                links=block["links"],
                source_selector=block["tag"],
            )
        )
    return fragments


def run_extract(layout):
    layout.ensure_base()
    extracted = {}
    for source_document_path in layout.documents_dir.glob("*/source_document.json"):
        document_dir = source_document_path.parent
        document_id = document_dir.name
        html = (document_dir / "raw.html").read_text(encoding="utf-8")
        fragments = parse_fragments(html)
        for fragment in fragments:
            fragment["document_id"] = document_id
            fragment["fragment_id"] = fragment["fragment_id"].replace("document", document_id, 1)
        output_path = layout.fragments_dir / document_id / "fragments.json"
        write_json(output_path, fragments)
        extracted[document_id] = fragments
    return extracted
