import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from system_design_space_importer.jsonio import write_json
from system_design_space_importer.robots import DEFAULT_USER_AGENT, fetch_robots_policy
from system_design_space_importer.utils import utc_now_iso


def build_discovery_policy(profile="chapters_only"):
    allowed_path_prefixes = ["/chapter/"]
    if profile != "chapters_only":
        allowed_path_prefixes = ["/chapter/"]

    return {
        "profile": profile,
        "allowed_path_prefixes": allowed_path_prefixes,
        "deduplicate_urls": True,
        "canonical_base_url": "https://system-design.space",
    }


def build_fetch_policy(
    profile="chapters_only",
    timeout_s=10,
    max_retries=1,
    rate_limit_ms=250,
    allow_file_scheme=True,
):
    return {
        "profile": profile,
        "allowed_hostnames": ["system-design.space", "www.system-design.space"],
        "allow_file_scheme": allow_file_scheme,
        "timeout_s": timeout_s,
        "max_retries": max_retries,
        "rate_limit_ms": rate_limit_ms,
    }


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


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


def _read_seed_source(seed, fetch_policy):
    parsed = urlparse(seed)
    scheme = parsed.scheme.lower()
    if scheme == "file":
        return Path(parsed.path).read_text(encoding="utf-8")

    if scheme not in ("http", "https"):
        raise ValueError("unsupported discovery seed scheme: {0}".format(scheme))

    hostname = (parsed.hostname or "").lower()
    if hostname not in fetch_policy["allowed_hostnames"]:
        raise ValueError("disallowed discovery host: {0}".format(hostname))

    with urlopen(seed, timeout=fetch_policy["timeout_s"]) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _extract_link_hrefs(html):
    parser = LinkExtractor()
    parser.feed(_extract_html_block(html))
    return parser.hrefs


def _is_allowed_path(path, discovery_policy):
    allowed_prefixes = discovery_policy["allowed_path_prefixes"]
    return any(path.startswith(prefix) for prefix in allowed_prefixes)


def _normalize_candidate_url(seed, href, fetch_policy, discovery_policy):
    if href.startswith(("#", "mailto:", "javascript:")):
        return None

    parsed_seed = urlparse(seed)
    canonical_base_url = discovery_policy["canonical_base_url"]

    if href.startswith("/"):
        candidate = urljoin(canonical_base_url, href)
    elif parsed_seed.scheme == "file":
        candidate = urljoin(canonical_base_url + "/", href)
    else:
        candidate = urljoin(seed, href)

    parsed_candidate = urlparse(candidate)
    scheme = parsed_candidate.scheme.lower()
    hostname = (parsed_candidate.hostname or "").lower()

    if scheme not in ("http", "https"):
        return None
    if hostname not in fetch_policy["allowed_hostnames"]:
        return None
    if not _is_allowed_path(parsed_candidate.path, discovery_policy):
        return None

    return parsed_candidate._replace(fragment="").geturl()


def _deduplicate_preserve_order(urls):
    seen = set()
    ordered = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        ordered.append(url)
    return ordered


def discover_urls(seed, profile="chapters_only", max_pages=None, fetch_policy=None):
    fetch_policy = fetch_policy or build_fetch_policy(profile=profile)
    discovery_policy = build_discovery_policy(profile=profile)
    parsed_seed = urlparse(seed)

    if parsed_seed.scheme in ("http", "https") and _is_allowed_path(
        parsed_seed.path, discovery_policy
    ):
        urls = [seed]
    else:
        html = _read_seed_source(seed, fetch_policy)
        urls = []
        for href in _extract_link_hrefs(html):
            candidate = _normalize_candidate_url(seed, href, fetch_policy, discovery_policy)
            if candidate is not None:
                urls.append(candidate)

        if discovery_policy["deduplicate_urls"]:
            urls = _deduplicate_preserve_order(urls)

        # Local file fixtures may represent either an index page or a direct
        # source page. If no allowed links were discovered, keep the seed itself
        # as the bounded target so chapter fixtures continue to work.
        if not urls and parsed_seed.scheme == "file":
            urls = [seed]

    if max_pages is not None:
        urls = urls[: max_pages if max_pages >= 0 else 0]
    return urls


def run_discovery(
    layout,
    seed,
    profile="chapters_only",
    max_pages=None,
    timeout_s=10,
    max_retries=1,
    rate_limit_ms=250,
):
    layout.ensure_base()
    fetch_policy = build_fetch_policy(
        profile=profile,
        timeout_s=timeout_s,
        max_retries=max_retries,
        rate_limit_ms=rate_limit_ms,
    )
    discovery_policy = build_discovery_policy(profile=profile)
    robots_policy = fetch_robots_policy(seed, fetch_policy, user_agent=DEFAULT_USER_AGENT)
    urls = discover_urls(
        seed=seed,
        profile=profile,
        max_pages=max_pages,
        fetch_policy=fetch_policy,
    )
    manifest = {
        "run_id": layout.run_id,
        "created_at": utc_now_iso(),
        "profile": profile,
        "seed": seed,
        "urls": urls,
        "fetch_policy": fetch_policy,
        "discovery_policy": discovery_policy,
        "robots_policy": robots_policy,
    }
    write_json(layout.manifest_path, manifest)
    return manifest
