from system_design_space_importer.jsonio import write_json
from system_design_space_importer.utils import utc_now_iso


def discover_urls(seed, profile="chapters_only", max_pages=None):
    urls = [seed]
    if max_pages is not None:
        urls = urls[: max_pages if max_pages >= 0 else 0]
    return urls


def run_discovery(layout, seed, profile="chapters_only", max_pages=None):
    layout.ensure_base()
    urls = discover_urls(seed=seed, profile=profile, max_pages=max_pages)
    manifest = {
        "run_id": layout.run_id,
        "created_at": utc_now_iso(),
        "profile": profile,
        "seed": seed,
        "urls": urls,
    }
    write_json(layout.manifest_path, manifest)
    return manifest
