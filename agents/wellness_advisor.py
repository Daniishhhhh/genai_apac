"""
wellness_advisor.py — WellnessAdvisorAgent (Phase 3A)
"""

import os, json, copy                          # copy at top — fixes NameError
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from schemas.label_schema import NutrientData, ConsumptionVerdict

from agents.nutri_score import compute_nutri_score

# ── Indian RDA constants ──────────────────────────────────────────────────────
RDA = {
    "calories_kcal":   2000,
    "total_sugars_g":  50,
    "sodium_mg":       2000,
    "saturated_fat_g": 22,
    "protein_g":       60,
    "fiber_g":         30,
}
SUGAR_TSP = 4.0

FRUIT_KEYWORDS = [
    "mango","apple","orange","pineapple","strawberry","guava","banana",
    "papaya","grape","lemon","lime","mixed fruit","real fruit",
    "fruit pulp","fruit juice",
]

COLOUR_INS = [
    "ins 102","ins 110","ins 122","ins 124","ins 129",
    "tartrazine","sunset yellow","carmoisine","ponceau","allura red",
]


# ── Verdict classifier ────────────────────────────────────────────────────────

def _get_verdict(grade: str, nutrients: NutrientData, high_flags: int):
    sodium = nutrients.sodium_mg or 0
    sugar  = nutrients.total_sugars_g or 0

    if high_flags > 0:
        return ConsumptionVerdict.RARE, f"Product has {high_flags} FSSAI compliance violation(s)"
    if grade == "E":
        return ConsumptionVerdict.RARE, "NutriScore E — very poor nutritional profile"
    if grade == "D":
        return ConsumptionVerdict.RARE, "NutriScore D — poor nutritional profile"
    if sodium > 400 or sugar > 15:
        spike = []
        if sodium > 400: spike.append(f"high sodium ({sodium:.0f}mg/100g)")
        if sugar  > 15:  spike.append(f"high sugar ({sugar:.1f}g/100g)")
        if grade in ("A","B"):
            return ConsumptionVerdict.OCCASIONAL, f"Grade {grade} but {' and '.join(spike)}"
        return ConsumptionVerdict.OCCASIONAL, f"NutriScore {grade} with {' and '.join(spike)}"
    if grade in ("A","B"):
        return ConsumptionVerdict.REGULAR, f"NutriScore {grade} — good nutritional profile"
    return ConsumptionVerdict.OCCASIONAL, "NutriScore C — moderate nutritional profile"


# ── Daily comparison sentences ────────────────────────────────────────────────

def _daily_comparisons(nutrients: NutrientData) -> list:
    out = []
    if nutrients.total_sugars_g is not None:
        pct  = round((nutrients.total_sugars_g / RDA["total_sugars_g"]) * 100)
        tsps = round(nutrients.total_sugars_g / SUGAR_TSP, 1)
        out.append(
            f"{nutrients.total_sugars_g}g sugar per 100g = {tsps} teaspoons "
            f"({pct}% of WHO daily limit of {RDA['total_sugars_g']}g)"
        )
    if nutrients.sodium_mg is not None:
        pct = round((nutrients.sodium_mg / RDA["sodium_mg"]) * 100)
        out.append(
            f"{nutrients.sodium_mg:.0f}mg sodium per 100g = {pct}% of daily limit "
            f"({RDA['sodium_mg']}mg ICMR recommendation)"
        )
    if nutrients.saturated_fat_g is not None:
        pct = round((nutrients.saturated_fat_g / RDA["saturated_fat_g"]) * 100)
        out.append(
            f"{nutrients.saturated_fat_g}g saturated fat per 100g = {pct}% of daily limit"
        )
    if nutrients.calories_kcal is not None:
        pct = round((nutrients.calories_kcal / RDA["calories_kcal"]) * 100)
        out.append(
            f"{nutrients.calories_kcal:.0f} kcal per 100g = {pct}% of a 2000 kcal daily diet"
        )
    return out


# ── Main tool ─────────────────────────────────────────────────────────────────

def generate_wellness_report(combined_json: str) -> dict:
    """
    Expects JSON string:
    {
        "label":        { ...ExtractedLabel fields... },
        "audit":        { ...audit result fields... },
        "user_profile": "general" | "diabetic" | "child" | "pregnant" | "lactose_intolerant"
    }
    Falls back gracefully if label JSON is passed directly without wrapper.
    """
    # ── Parse ──────────────────────────────────────────────────────────────────
    try:
        data = json.loads(combined_json)
    except Exception as e:
        return {"error": f"Invalid JSON: {e}"}

    # Support both wrapped {"label": {...}} and flat label JSON
    if "label" in data:
        label_dict   = data["label"]
        audit_dict   = data.get("audit", {})
        user_profile = data.get("user_profile", "general").lower()
    else:
        # Agent passed the label JSON directly
        label_dict   = data
        audit_dict   = {}
        user_profile = "general"

    # ── Extract fields — ALL defined before any use ───────────────────────────
    raw_nutrients    = label_dict.get("nutrients", {})
    ingredients      = label_dict.get("ingredients", [])
    ingredients_lower = [i.lower() for i in ingredients]
    high_flags       = audit_dict.get("high_severity_count", 0)

    # Parse nutrients safely
    try:
        nutrients = NutrientData(**raw_nutrients)
    except Exception:
        nutrients = NutrientData()

    # ── Estimate fruit % from ingredient position ──────────────────────────────
    fruit_pct = 0.0
    for i, ing in enumerate(ingredients_lower):
        if any(fk in ing for fk in FRUIT_KEYWORDS):
            fruit_pct = max(0.0, 50.0 - (i * 15.0))
            break

    # ── Profile overrides — work on a copy so original is unchanged ───────────
    scoring_nutrients = copy.copy(nutrients)

    if user_profile == "diabetic":
        if scoring_nutrients.total_sugars_g:
            scoring_nutrients.total_sugars_g *= 2.0   # halved effective threshold

    elif user_profile in ("child", "child (under 12)"):
        has_colour = any(c in " ".join(ingredients_lower) for c in COLOUR_INS)
        if has_colour:
            high_flags = max(high_flags, 1)            # auto-escalate verdict

    # ── NutriScore (pure arithmetic) ──────────────────────────────────────────
    ns = compute_nutri_score(scoring_nutrients, fruit_pct)
    grade = ns["grade"]

    # ── Verdict ───────────────────────────────────────────────────────────────
    verdict, reason = _get_verdict(grade, scoring_nutrients, high_flags)

    # ── Daily comparisons ─────────────────────────────────────────────────────
    comparisons = _daily_comparisons(nutrients)

    return {
        "product_name":           label_dict.get("product_name", "Unknown"),
        "brand":                  label_dict.get("brand", "Unknown"),
        "nutri_score":            grade,
        "nutri_score_points":     ns["score"],
        "nutri_score_breakdown":  ns["breakdown"],
        "consumption_verdict":    verdict.value,
        "verdict_reason":         reason,
        "daily_comparison":       comparisons,
        "user_profile":           user_profile,
        # body_impact written by the LLM in the instruction below
    }


wellness_tool = FunctionTool(func=generate_wellness_report)

WellnessAdvisorAgent = LlmAgent(
    name="WellnessAdvisorAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Generates NutriScore, consumption verdict, and plain-English health impact.",
    instruction="""You are the Chief Medical Officer and Registered Dietitian.

Step 1: Extract the label JSON and audit results. Call the generate_wellness_report tool.

Step 2: CRITICAL OVERRIDE RULE. Review the calculated Nutri-Score math. Look at 'mandatory_warnings' and 'flags'. If the user profile is "Child (under 12)" or "Pregnant" AND the product contains warnings about Caffeine, Taurine, or "Not recommended", YOU MUST override the Nutri-Score to "E" and set consumption_verdict to "Strictly Avoid". 

Step 3: Add the "body_impact" dictionary.
CRITICAL FORMATTING: "benefits" and "concerns" MUST BE JSON ARRAYS OF STRINGS (lists). 
- NEVER ABORT OR OUTPUT PLAIN TEXT. Even if the 'ingredients' list is empty, you MUST still output the JSON structure. Base your 'concerns' on the 'mandatory_warnings' and 'nutrients' (e.g., if sugar is high, flag it).
- Start every concern string with a warning word (e.g., "CAFFEINE:", "HIGH SUGAR:").
- For concerns, always say "at regular daily consumption". NEVER diagnose.

Step 4: Return the complete JSON with body_impact added.""",
    tools=[wellness_tool], # Ensure your tool name matches here
)