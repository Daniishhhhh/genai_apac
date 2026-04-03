"""
education_agent.py — EducationAgent (Phase 3B)

Queries ingredient_health_map, detects deceptive claims, 
suggests Indian kitchen swaps.
"""

import os, json, re
import sqlalchemy
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from tools.fssai_rag_tool import get_db_connection


# ── DB query ──────────────────────────────────────────────────────────────────

def _query_ingredient_map(ingredients: list[str]) -> list[dict]:
    """Look up each ingredient in ingredient_health_map (case-insensitive partial match)."""
    engine = get_db_connection()
    matches = []
    seen = set()
    with engine.connect() as conn:
        for ing in ingredients:
            result = conn.execute(
                sqlalchemy.text("""
                    SELECT ingredient_name, health_concern, natural_alternative, risk_level
                    FROM ingredient_health_map
                    WHERE LOWER(:ing) LIKE CONCAT('%', LOWER(ingredient_name), '%')
                       OR LOWER(ingredient_name) LIKE CONCAT('%', LOWER(:ing), '%')
                    ORDER BY risk_level DESC
                    LIMIT 1
                """),
                {"ing": ing}
            ).fetchone()

            if result and result[0] not in seen:
                seen.add(result[0])
                matches.append({
                    "ingredient":   ing,
                    "matched_to":   result[0],
                    "concern":      result[1],
                    "alternative":  result[2],
                    "risk_level":   result[3],
                })
    return matches


# ── Deception detector ────────────────────────────────────────────────────────

DECEPTION_PATTERNS = [
    {
        "claim_keywords": ["made with real fruit", "real fruit", "contains fruit"],
        "check": "fruit_position",
        "description": "Claims real fruit but fruit appears late in ingredient list",
        "regulation": "FSSAI Advertising & Claims Rules, Regulation 7 — claims must not mislead"
    },
    {
        "claim_keywords": ["no added sugar", "sugar free", "zero sugar"],
        "check": "hidden_sugar_aliases",
        "description": "Claims no sugar but contains sugar aliases in ingredients",
        "regulation": "FSSAI Schedule I, Row 10 — sugar-free threshold: ≤0.5g/100g"
    },
    {
        "claim_keywords": ["high protein", "protein rich", "rich in protein"],
        "check": "protein_threshold",
        "description": "Claims high protein but protein is below FSSAI threshold of 10g/100g",
        "regulation": "FSSAI Schedule I, Row 11 — high protein: ≥10g/100g"
    },
    {
        "claim_keywords": ["whole grain", "multigrain", "made with whole wheat"],
        "check": "grain_position",
        "description": "Claims whole grain but refined flour/maida appears before whole grain in ingredients",
        "regulation": "FSSAI Advertising & Claims Rules, Regulation 7"
    },
    {
        "claim_keywords": ["natural", "all natural", "100% natural"],
        "check": "artificial_in_ingredients",
        "description": "Claims natural but contains artificial colours, flavours, or preservatives",
        "regulation": "FSSAI Advertising & Claims Rules, Regulation 7"
    },
]

SUGAR_ALIASES = [
    "dextrose", "fructose", "glucose", "maltose", "sucrose", "galactose",
    "corn syrup", "hfcs", "high fructose", "invert sugar", "malt syrup",
    "molasses", "cane juice", "fruit juice concentrate", "evaporated cane",
    "agave", "brown rice syrup", "barley malt",
]

FRUIT_WORDS = ["mango", "apple", "orange", "pineapple", "strawberry", "guava",
               "banana", "papaya", "grape", "lemon", "lime", "mixed fruit",
               "fruit pulp", "fruit juice", "real fruit"]

REFINED_GRAINS = ["maida", "refined wheat flour", "refined flour", "all purpose flour"]
WHOLE_GRAINS   = ["whole wheat", "whole grain", "oats", "ragi", "jowar", "bajra", "barley"]
ARTIFICIAL     = ["artificial colour", "artificial flavor", "artificial flavour",
                  "ins 102", "ins 110", "ins 122", "ins 124", "ins 129",
                  "tartrazine", "sunset yellow", "carmoisine", "allura red"]


def _check_deception(claims: list[str], ingredients: list[str], nutrients: dict) -> list[dict]:
    flags = []
    claims_lower    = [c.lower() for c in claims]
    ingredients_lower = [i.lower() for i in ingredients]
    ingredients_str = " ".join(ingredients_lower)

    for pattern in DECEPTION_PATTERNS:
        matched_claim = next(
            (c for c in claims_lower if any(k in c for k in pattern["claim_keywords"])),
            None
        )
        if not matched_claim:
            continue

        check   = pattern["check"]
        flagged = False

        if check == "fruit_position":
            # Flag if first fruit word appears at position ≥ 3 (0-indexed)
            for i, ing in enumerate(ingredients_lower):
                if any(f in ing for f in FRUIT_WORDS):
                    if i >= 3:
                        flagged = True
                    break
            else:
                flagged = True  # no fruit found at all

        elif check == "hidden_sugar_aliases":
            flagged = any(alias in ingredients_str for alias in SUGAR_ALIASES)

        elif check == "protein_threshold":
            protein = nutrients.get("protein_g")
            flagged = (protein is not None and protein < 10.0)

        elif check == "grain_position":
            first_refined = next(
                (i for i, ing in enumerate(ingredients_lower) if any(r in ing for r in REFINED_GRAINS)), None
            )
            first_whole = next(
                (i for i, ing in enumerate(ingredients_lower) if any(w in ing for w in WHOLE_GRAINS)), None
            )
            if first_refined is not None and (first_whole is None or first_refined < first_whole):
                flagged = True

        elif check == "artificial_in_ingredients":
            flagged = any(a in ingredients_str for a in ARTIFICIAL)

        if flagged:
            flags.append({
                "claim":       matched_claim,
                "issue":       pattern["description"],
                "regulation":  pattern["regulation"],
                "severity":    "medium",
            })

    return flags


# ── Main tool ─────────────────────────────────────────────────────────────────

def analyse_ingredients(label_json: str) -> dict:
    """
    Input: ExtractedLabel JSON string
    Output: {
        "flagged_ingredients": [...],
        "deception_flags": [...],
        "high_risk_count": int,
        "medium_risk_count": int,
        "swap_suggestions": [{"ingredient": ..., "swap": ..., "risk": ...}]
    }
    """
    try:
        label = json.loads(label_json)
    except Exception as e:
        return {"error": str(e)}

    ingredients = label.get("ingredients", [])
    claims      = label.get("health_claims", [])
    nutrients   = label.get("nutrients", {})

    # DB lookup
    flagged = _query_ingredient_map(ingredients)

    # Deception check
    deception = _check_deception(claims, ingredients, nutrients)

    # Build swap suggestions for high/medium risk only
    swaps = [
        {
            "ingredient": f["ingredient"],
            "matched_to": f["matched_to"],
            "concern":    f["concern"],
            "swap":       f["alternative"],
            "risk_level": f["risk_level"],
        }
        for f in flagged if f["risk_level"] in ("High", "Medium")
    ]

    high_count   = sum(1 for f in flagged if f["risk_level"] == "High")
    medium_count = sum(1 for f in flagged if f["risk_level"] == "Medium")

    return {
        "product_name":       label.get("product_name", "Unknown"),
        "flagged_ingredients": flagged,
        "deception_flags":    deception,
        "high_risk_count":    high_count,
        "medium_risk_count":  medium_count,
        "swap_suggestions":   swaps,
    }


education_tool = FunctionTool(func=analyse_ingredients)

EducationAgent = LlmAgent(
    name="EducationAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Flags harmful ingredients, detects deceptive claims, suggests Indian kitchen alternatives.",
    instruction="""You are a Strict Clinical Dietitian and Toxicologist helping Indian consumers. You evaluate food labels based explicitly on the user's selected health profile (General, Diabetic, Child under 12, Pregnant, Hypertension).

Step 1: Call analyse_ingredients with the extracted label JSON string.

CRITICAL DEFENSIVE CHECK: NEVER abort or output plain text. YOU MUST STILL RETURN THE FULL JSON STRUCTURE. If the 'ingredients' list is empty or unreadable, use the 'mandatory_warnings' and 'nutrients' to populate your report (e.g., if a warning says "Contains caffeine", you must still flag Caffeine!).

Step 2: Generate a comprehensive health report by populating the JSON fields:

1. PROFILE-SPECIFIC TRIAGE & WARNINGS:
   - Child (<12): Zero tolerance for caffeine, artificial colors (Tartrazine, Sunset Yellow), or high sugars.
   - Pregnant: Zero tolerance for caffeine, unpasteurized elements, or heavy chemical preservatives.
   - Diabetic: Strict warning on added sugars, maltodextrin, and refined carbs (Maida).
   - Hypertension: Strict warning on high sodium (>200mg/serving) and hidden salts.

2. SMART SWAPS & GRADING (flagged_ingredients array):
   You MUST populate the 'flagged_ingredients' JSON array. It CANNOT be empty if the product contains ultra-processed elements or FSSAI warnings.
   - For every flagged item, the 'concern' field must explicitly state the biological harm based on the user's profile.
   - The 'alternative' field must provide a realistic, whole-food Indian alternative (e.g., Coconut Water, Jaggery, Nimbu Pani) and explain the benefit of switching.

3. PRESERVATIVE IMPACT SUMMARY:
   Write 2-3 sentences explaining what the high/medium risk chemicals (or warned items) do to the body over time with regular consumption. Mention specific chemicals by name. Explicitly state a safe CONSUMPTION LIMIT here (e.g., "Strictly Avoid", "Maximum 1 serving (30g) per week").

4. DECEPTION SUMMARY:
   Write 1-2 sentences explaining misleading claims, if any.

Return the full, structured JSON result. Keep the tone highly professional, uncompromising on health, and specifically tailored to the user's age and medical condition. Do not be overly optimistic about ultra-processed foods.
""",
    tools=[education_tool],
)