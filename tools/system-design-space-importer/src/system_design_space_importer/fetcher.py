import re
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from system_design_space_importer import __version__
from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.models import source_document
from system_design_space_importer.utils import sha256_text, slugify, strip_whitespace, utc_now_iso


def _read_source(url):
    parsed = urlparse(url)
    if parsed.scheme == "file":
        path = Path(parsed.path)
        html = path.read_text(encoding="utf-8")
        return html, 200, "text/html"

    with urlopen(url) as response:
        raw = response.read()
        content_type = response.headers.get_content_type() or "application/octet-stream"
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), response.status, content_type


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


def normalize_html_text(html):
    block = _extract_html_block(html)
    stripped = re.sub(r"<script\b[^>]*>.*?</script>", " ", block, flags=re.IGNORECASE | re.DOTALL)
    stripped = re.sub(r"<style\b[^>]*>.*?</style>", " ", stripped, flags=re.IGNORECASE | re.DOTALL)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    return strip_whitespace(unescape(stripped))


def document_id_from_url(url):
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return slugify(Path(parsed.path).stem)
    path = parsed.path.rstrip("/")
    slug = path.split("/")[-1] if path else parsed.netloc
    return slugify(slug)


def run_fetch(layout):
    layout.ensure_base()
    manifest = read_json(layout.manifest_path)
    documents = []

    for url in manifest["urls"]:
        html, status, content_type = _read_source(url)
        normalized_text = normalize_html_text(html)
        document_id = document_id_from_url(url)
        document_dir = layout.documents_dir / document_id
        raw_html_path = document_dir / "raw.html"
        normalized_text_path = document_dir / "normalized.txt"
        raw_html_path.parent.mkdir(parents=True, exist_ok=True)
        raw_html_path.write_text(html, encoding="utf-8")
        normalized_text_path.write_text(normalized_text, encoding="utf-8")

        document = source_document(
            document_id=document_id,
            source_name="system-design.space",
            source_url=url,
            canonical_url=url,
            discovered_from=manifest["seed"],
            fetched_at=utc_now_iso(),
            fetch_mode="http_only" if not url.startswith("file://") else "file",
            http_status=status,
            content_type=content_type,
            source_hash=sha256_text(normalized_text),
            raw_html_path=str(raw_html_path.relative_to(layout.base_dir)),
            normalized_text_path=str(normalized_text_path.relative_to(layout.base_dir)),
            parser_version=__version__,
            charset="utf-8",
        )
        write_json(document_dir / "source_document.json", document)
        documents.append(document)

    return documents
