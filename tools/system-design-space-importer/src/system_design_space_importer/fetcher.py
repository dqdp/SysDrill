import re
import time
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from system_design_space_importer import __version__
from system_design_space_importer.discovery import build_fetch_policy
from system_design_space_importer.jsonio import read_json, write_json
from system_design_space_importer.models import source_document
from system_design_space_importer.utils import sha256_text, slugify, strip_whitespace, utc_now_iso


def _validate_url_against_policy(url, policy):
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme == "file":
        if not policy.get("allow_file_scheme", False):
            raise ValueError("file scheme is not allowed by fetch policy")
        return

    if scheme not in ("http", "https"):
        raise ValueError("unsupported scheme: {0}".format(scheme))

    hostname = (parsed.hostname or "").lower()
    allowed_hostnames = policy.get("allowed_hostnames", [])
    if hostname not in allowed_hostnames:
        raise ValueError("disallowed host: {0}".format(hostname))


def _read_file_source(url):
    path = Path(urlparse(url).path)
    html = path.read_text(encoding="utf-8")
    return html, 200, "text/html"


def _read_http_source(url, timeout_s):
    with urlopen(url, timeout=timeout_s) as response:
        raw = response.read()
        content_type = response.headers.get_content_type() or "application/octet-stream"
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), response.status, content_type


def _sleep_for_rate_limit(rate_limit_ms):
    if rate_limit_ms > 0:
        time.sleep(rate_limit_ms / 1000.0)


def _effective_rate_limit_ms(policy, robots_policy):
    base_rate_limit_ms = policy.get("rate_limit_ms", 250)
    crawl_delay_s = None
    if robots_policy:
        crawl_delay_s = robots_policy.get("crawl_delay_s")

    robots_rate_limit_ms = int(crawl_delay_s * 1000) if crawl_delay_s is not None else 0
    return max(base_rate_limit_ms, robots_rate_limit_ms)


def _read_source(url, policy, robots_policy=None):
    _validate_url_against_policy(url, policy)
    parsed = urlparse(url)
    if parsed.scheme.lower() == "file":
        html, status, content_type = _read_file_source(url)
        return html, status, content_type, 1

    timeout_s = policy.get("timeout_s", 10)
    max_retries = policy.get("max_retries", 1)
    rate_limit_ms = _effective_rate_limit_ms(policy, robots_policy)
    max_attempts = max_retries + 1
    last_error = None

    for attempt_count in range(1, max_attempts + 1):
        _sleep_for_rate_limit(rate_limit_ms)
        try:
            html, status, content_type = _read_http_source(url, timeout_s)
            return html, status, content_type, attempt_count
        except Exception as exc:
            last_error = exc
            if attempt_count == max_attempts:
                raise

    raise last_error


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
    policy = manifest.get("fetch_policy") or build_fetch_policy(profile=manifest.get("profile"))
    robots_policy = manifest.get("robots_policy")
    documents = []

    for url in manifest["urls"]:
        html, status, content_type, attempt_count = _read_source(url, policy, robots_policy)
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
            fetch_metadata={
                "policy_name": policy.get("profile", manifest.get("profile")),
                "timeout_s": policy.get("timeout_s", 10),
                "max_retries": policy.get("max_retries", 1),
                "rate_limit_ms": policy.get("rate_limit_ms", 250),
                "effective_rate_limit_ms": _effective_rate_limit_ms(policy, robots_policy),
                "robots_crawl_delay_s": (
                    robots_policy.get("crawl_delay_s") if robots_policy is not None else None
                ),
                "attempt_count": attempt_count,
            },
        )
        write_json(document_dir / "source_document.json", document)
        documents.append(document)

    return documents
