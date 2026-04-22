import csv
import os
import re
from functools import lru_cache

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "strains.csv")

VALID_TYPES = {"Hybrid", "Indica", "Sativa"}


def _load():
    strains = []
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["type"] not in VALID_TYPES:
                continue
            strains.append({
                "name":     row["name"],
                "type":     row["type"],
                "effects":  _split(row["effects"]),
                "flavors":  _split(row["flavor"]),
                "terpenes": _split(row["terpenes"]),
                "thc":      _pct(row["thc"]),
                "cbd":      _pct(row["cbd"]),
                "description": _strip_html(row.get("description") or ""),
                "breeder":  row.get("breeder") or "",
            })
    return strains


def _split(val):
    if not val or val.strip().upper() in ("NULL", ""):
        return []
    return [v.strip() for v in val.split(",") if v.strip() and v.strip().upper() != "NULL"]


def _pct(val):
    try:
        v = float(val)
        # 127 is a sentinel "unknown" value in this dataset
        if v == 127 or v == 0:
            return None
        # Values are stored as integers (e.g. 1300 = 13.00%)
        if v > 100:
            v = v / 100
        return round(v, 1)
    except (TypeError, ValueError):
        return None


def _strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()


# Load once at import time
_STRAINS = _load()

# Build lookup sets for fast matching
_BY_TYPE = {}
for s in _STRAINS:
    _BY_TYPE.setdefault(s["type"], []).append(s)


def search(
    strain_type: str | None = None,
    effects: list[str] | None = None,
    flavors: list[str] | None = None,
    top_n: int = 5,
) -> list[dict]:
    """
    Return up to top_n strains scored by how well they match the given
    type / effects / flavors. All arguments are optional.
    """
    pool = _STRAINS

    # Filter by type first (big speed-up, keeps results relevant)
    if strain_type and strain_type in VALID_TYPES:
        pool = _BY_TYPE.get(strain_type, [])

    effects_lower  = [e.lower() for e in (effects  or [])]
    flavors_lower  = [f.lower() for f in (flavors  or [])]

    scored = []
    for s in pool:
        score = 0
        s_effects = [e.lower() for e in s["effects"]]
        s_flavors = [f.lower() for f in s["flavors"]]

        for e in effects_lower:
            if any(e in se for se in s_effects):
                score += 2
        for f in flavors_lower:
            if any(f in sf for sf in s_flavors):
                score += 1

        # Prefer strains that have actual THC data
        if s["thc"] is not None:
            score += 0.5

        # Prefer strains with descriptions
        if s["description"]:
            score += 0.3

        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    results = [s for _, s in scored[:top_n]]
    return results


def total_strains() -> int:
    return len(_STRAINS)
