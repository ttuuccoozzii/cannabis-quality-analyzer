import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "seed_diseases.json")

with open(DATA_PATH) as f:
    _SEED_DISEASES = json.load(f)

_BY_ID = {d["id"]: d for d in _SEED_DISEASES}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def get_names() -> list[str]:
    return [d["name"] for d in _SEED_DISEASES]


def lookup_by_name(name: str) -> dict | None:
    name_lower = name.lower()
    for d in _SEED_DISEASES:
        if d["name"].lower() == name_lower:
            return d
    for d in _SEED_DISEASES:
        if name_lower in d["name"].lower() or d["id"].lower() in name_lower.replace(" ", "_"):
            return d
    return None


def format_disease(d: dict) -> dict:
    return {
        "id":                  d["id"],
        "name":                d["name"],
        "category":            d["category"],
        "severity":            d["severity"],
        "visual_symptoms":     d["visual_symptoms"],
        "causes":              d["causes"],
        "treatment":           d["treatment"],
        "germination_impact":  d["germination_impact"],
    }


def total() -> int:
    return len(_SEED_DISEASES)
