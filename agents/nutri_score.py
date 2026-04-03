"""
nutri_score.py — NutriScore A–E calculator adapted for Indian RDAs.
Accepts nutrients as either a NutrientData object OR a plain dict.
Includes aggressive type-coercion to prevent AI hallucination crashes.
"""

import re
from typing import Union

# ── Safe Number Extraction ────────────────────────────────────────────────────

def _to_float(val, default=0.0) -> float:
    """Safely extracts a float from mixed AI strings (e.g., '12.5g', 'N/A', None)."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        # Extracts the first valid number found in the string
        match = re.search(r"[-+]?\d*\.?\d+", str(val))
        if match:
            return float(match.group())
    except:
        pass
    return default

# ── Negative point tables (per 100g) ─────────────────────────────────────────

def _energy_points(kcal: float) -> int:
    thresholds = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]
    for i, t in enumerate(thresholds):
        if kcal <= t: return i
    return 10

def _sugar_points(g: float) -> int:
    thresholds = [4.5, 9, 13.5, 18, 22.5, 27, 31, 36, 40, 45]
    for i, t in enumerate(thresholds):
        if g <= t: return i
    return 10

def _satfat_points(g: float) -> int:
    thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for i, t in enumerate(thresholds):
        if g <= t: return i
    return 10

def _sodium_points(mg: float) -> int:
    thresholds = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900]
    for i, t in enumerate(thresholds):
        if mg <= t: return i
    return 10


# ── Positive point tables (per 100g) ─────────────────────────────────────────

def _protein_points(g: float) -> int:
    thresholds = [1.6, 3.2, 4.8, 6.4, 8.0]
    for i, t in enumerate(thresholds):
        if g <= t: return i
    return 5

def _fibre_points(g: float) -> int:
    thresholds = [0.9, 1.9, 2.8, 3.7, 4.7]
    for i, t in enumerate(thresholds):
        if g <= t: return i
    return 5

def _fruit_points(fruit_pct: float) -> int:
    if fruit_pct >= 80: return 5
    if fruit_pct >= 60: return 4
    if fruit_pct >= 40: return 2
    return 0


# ── Grade mapping ─────────────────────────────────────────────────────────────

def _score_to_grade(score: int) -> str:
    if score <= -1: return "A"
    if score <=  2: return "B"
    if score <= 10: return "C"
    if score <= 18: return "D"
    return "E"


# ── Nutrient accessor ─────────────────────────────────────────────────────────

def _get_val(nutrients, key: str, default=0.0) -> float:
    """Safe accessor: handles dict, Pydantic model, missing keys, and bad types."""
    raw_val = None
    if nutrients is None:
        raw_val = default
    elif isinstance(nutrients, dict):
        raw_val = nutrients.get(key, default)
    else:
        raw_val = getattr(nutrients, key, default)
    
    return _to_float(raw_val, default)


# ── Public API ────────────────────────────────────────────────────────────────

def compute_nutri_score(nutrients, fruit_pct: float = 0.0) -> dict:
    """
    Computes the Nutri-Score based on nutritional values.
    Accepts nutrients as a plain dict OR a NutrientData Pydantic object.
    """
    # 1. Safely extract and parse all values as floats
    e  = _energy_points(_get_val(nutrients, "calories_kcal"))
    s  = _sugar_points(_get_val(nutrients, "total_sugars_g"))
    f  = _satfat_points(_get_val(nutrients, "saturated_fat_g"))
    na = _sodium_points(_get_val(nutrients, "sodium_mg"))
    negative = e + s + f + na

    p  = _protein_points(_get_val(nutrients, "protein_g"))
    fi = _fibre_points(_get_val(nutrients, "fiber_g"))
    fr = _fruit_points(_to_float(fruit_pct))
    positive = p + fi + fr

    # 2. Apply Nutri-Score / FSSAI Logic Gate
    # Rule: If negative points >= 11, protein points are IGNORED unless fruit points == 5.
    if negative >= 11 and fr < 5:
        final_score = negative - fi - fr
    else:
        final_score = negative - positive

    return {
        "grade":           _score_to_grade(final_score),
        "score":           final_score,
        "negative_points": negative,
        "positive_points": positive,
        "breakdown": {
            "energy":  e,
            "sugars":  s,
            "sat_fat": f,
            "sodium":  na,
            "protein": p,
            "fibre":   fi,
            "fruit":   fr,
        }
    }