import json
from pathlib import Path


def write_json(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)
