import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "seed_strains.json")

with open(DATA_PATH) as f:
    _STRAINS = json.load(f)


def get_all() -> list[dict]:
    return _STRAINS


def total() -> int:
    return len(_STRAINS)


def reference_summary() -> str:
    """Return a compact description of all known healthy seed profiles for use in prompts."""
    lines = []
    for s in _STRAINS:
        lines.append(
            f"- {s['strain']}: {s['color']}, {s['markings']}, "
            f"{s['size']} size, {s['shape']} shape, {s['fullness']}"
        )
    return "\n".join(lines)
