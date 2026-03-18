import hashlib
import re
from datetime import datetime, timezone


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value):
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "untitled"


def sha256_text(value):
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def strip_whitespace(value):
    return re.sub(r"\s+", " ", value or "").strip()
