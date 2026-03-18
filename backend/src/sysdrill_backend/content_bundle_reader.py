from pathlib import Path

import yaml


class BundleLoadError(ValueError):
    pass


def _ensure_safe_export_root(export_root: str | Path) -> Path:
    candidate = Path(export_root)
    if ".." in candidate.parts:
        raise BundleLoadError("export root must not escape the configured export root")

    resolved = candidate.resolve()
    if not resolved.exists():
        raise BundleLoadError("export root does not exist: {0}".format(resolved))
    if not resolved.is_dir():
        raise BundleLoadError("export root is not a directory: {0}".format(resolved))
    return resolved


def _read_json(path: Path) -> dict:
    import json

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise BundleLoadError(
            "bundle JSON file must deserialize to an object: {0}".format(path.name)
        )
    return payload


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise BundleLoadError(
            "bundle YAML file must deserialize to a mapping: {0}".format(path.name)
        )
    return payload


def _required_file(topic_dir: Path, filename: str) -> Path:
    path = topic_dir / filename
    if path.is_symlink():
        raise BundleLoadError("symlinked bundle files are not allowed: {0}".format(path))
    if not path.exists():
        raise BundleLoadError("missing required bundle file: {0}".format(filename))
    if not path.is_file():
        raise BundleLoadError("bundle path is not a file: {0}".format(path))
    return path


def _load_bundle(topic_dir: Path, source_dir_name: str, allow_draft_bundles: bool) -> dict:
    if not allow_draft_bundles:
        raise BundleLoadError("draft bundle loading requires allow_draft_bundles=True")

    topic_package_path = _required_file(topic_dir, "topic-package.yaml")
    provenance_path = _required_file(topic_dir, "provenance.json")
    validation_report_path = _required_file(topic_dir, "validation-report.json")

    topic_package = _read_yaml(topic_package_path)
    provenance = _read_json(provenance_path)
    validation_report = _read_json(validation_report_path)

    topic_slug = topic_package.get("topic_slug")
    if topic_slug != topic_dir.name:
        raise BundleLoadError(
            "topic_slug mismatch for bundle directory '{0}'".format(topic_dir.name)
        )

    if not validation_report.get("schema_valid", False):
        raise BundleLoadError("bundle validation-report schema_valid is false")

    return {
        "topic_slug": topic_slug,
        "bundle_source_name": source_dir_name,
        "is_draft_bundle": True,
        "topic_package": topic_package,
        "provenance": provenance,
        "validation_report": validation_report,
    }


def _iter_bundle_dirs(parent: Path, directory_kind: str) -> list[Path]:
    directories = []
    for path in sorted(parent.iterdir()):
        if path.is_symlink() and path.is_dir():
            raise BundleLoadError(
                "symlinked {0} directories are not allowed: {1}".format(directory_kind, path)
            )
        if path.is_dir():
            directories.append(path)
    return directories


def load_topic_catalog(
    export_root: str | Path,
    allow_draft_bundles: bool = False,
) -> dict[str, dict]:
    root = _ensure_safe_export_root(export_root)
    catalog = {}
    bundle_count = 0

    for source_dir in _iter_bundle_dirs(root, "source"):
        for topic_dir in _iter_bundle_dirs(source_dir, "topic"):
            bundle = _load_bundle(topic_dir, source_dir.name, allow_draft_bundles)
            topic_slug = bundle["topic_slug"]
            if topic_slug in catalog:
                raise BundleLoadError("duplicate topic_slug detected: {0}".format(topic_slug))
            catalog[topic_slug] = bundle
            bundle_count += 1

    if bundle_count == 0:
        raise BundleLoadError("export root does not contain any topic bundles: {0}".format(root))

    return catalog
