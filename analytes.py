import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "analytes.json")

with open(DATA_PATH) as f:
    _RAW = json.load(f)

# ── Build lookup tables ────────────────────────────────────────────────────────

_BY_KEY  = {r["key"]: r for r in _RAW}
_BY_TYPE = {"cannabinoid": [], "terpene": []}
for r in _RAW:
    _BY_TYPE.get(r["type"], []).append(r)

def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())

# Alias map: normalised incoming name → analyte key
_ALIASES: dict[str, str] = {}
for r in _RAW:
    for label in [r["key"], r["name"], r.get("scientific_name") or ""]:
        if label:
            _ALIASES[_normalize(label)] = r["key"]

# Extra hand-written aliases for common Kushy terpene spellings
_EXTRA: dict[str, str] = {
    "limonene":         "d_limonene",
    "dlimonene":        "d_limonene",
    "myrcene":          "beta_myrcene",
    "betamyrcene":      "beta_myrcene",
    "pinene":           "alpha_pinene",
    "alphapinene":      "alpha_pinene",
    "betapinene":       "beta_pinene",
    "caryophyllene":    "beta_caryophyllene",
    "betacaryophyllene":"beta_caryophyllene",
    "humulene":         "humulene",
    "linalool":         "linalool",
    "terpinolene":      "terpinolene",
    "ocimene":          "ocimene",
    "bisabolol":        "alpha_bisabolol",
    "alphabisabolol":   "alpha_bisabolol",
    "eucalyptol":       "eucalyptol",
    "geraniol":         "geraniol",
    "nerolidol":        "nerolidol",
    "guaiol":           "guaiol",
    "camphene":         "camphene",
    "terpinene":        "gamma_terpinene",
    "cymene":           "p_cymene",
    "carene":           "carene",
    "isopulegol":       "isopulegol",
    "thc":              "delta_9_thc",
    "delta9thc":        "delta_9_thc",
    "delta8thc":        "delta_8_thc",
    "thca":             "thca",
    "cbg":              "cbg",
    "cbga":             "cbga",
    "cbn":              "cbn",
    "cbc":              "cbc",
    "cbdv":             "cbdv",
    "thcv":             "thcv",
    "thcva":            "thcva",
    "cbt":              "cbt",
    "cbl":              "cbl",
}
_ALIASES.update(_EXTRA)


# ── Public API ─────────────────────────────────────────────────────────────────

def lookup(name: str) -> dict | None:
    """Return analyte record for a name/alias, or None."""
    key = _ALIASES.get(_normalize(name))
    return _BY_KEY.get(key) if key else None


def get_terpenes() -> list[dict]:
    return _BY_TYPE["terpene"]


def get_cannabinoids() -> list[dict]:
    return _BY_TYPE["cannabinoid"]


def enrich_terpene_list(names: list[str]) -> list[dict]:
    """Given a list of terpene name strings, return enriched analyte dicts."""
    out = []
    seen = set()
    for n in names:
        rec = lookup(n)
        if rec and rec["key"] not in seen:
            seen.add(rec["key"])
            out.append(rec)
    return out


def format_analyte(r: dict) -> dict:
    """Slim down an analyte record for JSON response."""
    return {
        "key":            r["key"],
        "name":           r["name"],
        "scientific_name":r.get("scientific_name") or "",
        "type":           r["type"],
        "subtype":        r.get("subtype") or "",
        "chemical_formula": r.get("chemical_formula") or "",
        "molar_mass":     r.get("molar_mass") or "",
        "description":    (r.get("description") or "")[:300],
        "wikipedia_url":  r.get("wikipedia_url") or "",
        "degrades_to":    r.get("degrades_to") or [],
        "precursors":     r.get("precursors") or [],
    }
