import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "diseases.json")

with open(DATA_PATH) as f:
    _DISEASES = json.load(f)

_BY_ID = {d["id"]: d for d in _DISEASES}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def get_all() -> list[dict]:
    return _DISEASES


def get_names() -> list[str]:
    return [d["name"] for d in _DISEASES]


def lookup(disease_id: str) -> dict | None:
    return _BY_ID.get(disease_id)


def lookup_by_name(name: str) -> dict | None:
    name_lower = name.lower()
    for d in _DISEASES:
        if d["name"].lower() == name_lower or d["id"].lower() == name_lower.replace(" ", "_"):
            return d
    # Fuzzy: partial match
    for d in _DISEASES:
        if name_lower in d["name"].lower():
            return d
    return None


def format_disease(d: dict) -> dict:
    return {
        "id":               d["id"],
        "name":             d["name"],
        "category":         d["category"],
        "severity":         d["severity"],
        "causes":           d["causes"],
        "treatment":        d["treatment"],
        "risk_to_consumer": d["risk_to_consumer"],
        "visual_symptoms":  d["visual_symptoms"],
    }


def total() -> int:
    return len(_DISEASES)
