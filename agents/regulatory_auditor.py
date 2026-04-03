import os, json
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from tools.fssai_rag_tool import get_db_connection, query_fssai_regulations
import sqlalchemy
from typing import Optional

# ── Synonym map: any of these strings → one nutrient category ────────────────
CLAIM_SYNONYMS = {
    "sugar_claims": [
        "sugar free", "sugar-free", "zero sugar", "no sugar",
        "without sugar", "negligible sugar", "low sugar", "less sugar"
    ],
    "sodium_claims": [
        "low sodium", "reduced sodium", "no added salt", "sodium free",
        "low salt", "less sodium", "light salt"
    ],
    "fat_claims": [
        "fat free", "fat-free", "zero fat", "no fat", "low fat",
        "reduced fat", "light", "lite"
    ],
    "trans_fat_claims": [
        "trans fat free", "zero trans", "no trans fat", "0g trans"
    ],
    "protein_claims": [
        "high protein", "rich in protein", "protein rich",
        "good source of protein", "excellent source of protein"
    ],
}

# ── FSSAI hard limits (from Schedule I) ──────────────────────────────────────
HARD_LIMITS = {
    "sugar_claims":    {"nutrient": "total_sugars_g",  "limit": 0.5,  "unit": "g/100g", "ref": "Schedule I Row 10"},
    "sodium_claims":   {"nutrient": "sodium_mg",       "limit": 120,  "unit": "mg/100g","ref": "Schedule I Row 13"},
    "fat_claims":      {"nutrient": "saturated_fat_g", "limit": 0.5,  "unit": "g/100g", "ref": "Schedule I Row 2"},
    "trans_fat_claims":{"nutrient": "trans_fat_g",     "limit": 0.2,  "unit": "g/100g", "ref": "Schedule I Row 6"},
    "protein_claims":  {"nutrient": "protein_g",       "limit": 10.0, "unit": "g/100g", "ref": "Schedule I Row 11"},
}

def get_claim_group(claim: str) -> Optional[str]:
    """Map a claim string to its nutrient category."""
    claim_lower = claim.lower().strip()
    for group, synonyms in CLAIM_SYNONYMS.items():
        if any(syn in claim_lower for syn in synonyms):
            return group
    return None

def audit_label_claims(extracted_label_json: str) -> dict:
    try:
        label = json.loads(extracted_label_json)
    except Exception as e:
        return {"error": f"Invalid JSON: {e}"}

    nutrients  = label.get("nutrients", {})
    claims     = label.get("health_claims", [])
    flags      = []
    nutrient_context = (
        f"Sugars:{nutrients.get('total_sugars_g')}g, "
        f"Sodium:{nutrients.get('sodium_mg')}mg, "
        f"Fat:{nutrients.get('saturated_fat_g')}g sat, "
        f"Trans:{nutrients.get('trans_fat_g')}g, "
        f"Protein:{nutrients.get('protein_g')}g"
    )

    # ── Step A: pre-compute which nutrient groups are violated ────────────────
    violated_groups = set()
    for group, limits in HARD_LIMITS.items():
        nutrient_key = limits["nutrient"]
        actual_value = nutrients.get(nutrient_key)
        if actual_value is not None and actual_value > limits["limit"]:
            violated_groups.add(group)

    # ── Step B: audit each claim ──────────────────────────────────────────────
    for claim in claims:
        group = get_claim_group(claim)
        rag   = query_fssai_regulations(claim, nutrient_context)

        if group and group in violated_groups:
            # Hard-limit violation — force fail regardless of RAG result
            limits  = HARD_LIMITS[group]
            actual  = nutrients.get(limits["nutrient"])
            flags.append({
                "claim":                claim,
                "status":               "non_compliant",
                "severity":             "high",
                "nutrient_group":       group,
                "actual_value":         actual,
                "fssai_limit":          limits["limit"],
                "unit":                 limits["unit"],
                "explanation":          (
                    f"HARD LIMIT VIOLATED: '{claim}' claims {limits['unit']} ≤{limits['limit']} "
                    f"but actual value is {actual} {limits['unit']}. "
                    f"FSSAI {limits['ref']}."
                ),
                "regulation_reference": rag.get("regulation_text", "")[:200],
                "rag_similarity":       rag.get("similarity_score", 0),
                "detection_method":     "constraint_hard_limit",
            })
        elif not rag.get("found"):
            flags.append({
                "claim":            claim,
                "status":           "needs_review",
                "severity":         "low",
                "nutrient_group":   group or "unknown",
                "explanation":      f"No FSSAI regulation matched for '{claim}'. Manual review needed.",
                "detection_method": "rag_no_match",
            })
        else:
            flags.append({
                "claim":                claim,
                "status":               "compliant",
                "severity":             "low",
                "nutrient_group":       group or "unknown",
                "explanation":          f"'{claim}' is consistent with FSSAI regulations.",
                "regulation_reference": rag.get("regulation_text", "")[:200],
                "rag_similarity":       rag.get("similarity_score", 0),
                "detection_method":     "rag_match",
            })

    # ── Step C: override scoring ──────────────────────────────────────────────
    high_flags   = [f for f in flags if f["severity"] == "high"]
    medium_flags = [f for f in flags if f["severity"] == "medium"]
    base_score   = (len(high_flags) * 35) + (len(medium_flags) * 15)

    # Override rule: any high flag → minimum score 80
    risk_score   = max(80, base_score) if high_flags else min(base_score, 79)
    overall      = "non_compliant" if high_flags else (
                   "needs_review"  if medium_flags else "compliant"
                   )

    return {
        "product_name":          label.get("product_name", "Unknown"),
        "brand":                 label.get("brand", "Unknown"),
        "flags":                 flags,
        "overall_status":        overall,
        "risk_score":            risk_score,
        "total_claims_checked":  len(claims),
        "high_severity_count":   len(high_flags),
        "medium_severity_count": len(medium_flags),
        "violated_groups":       list(violated_groups),
    }

audit_tool = FunctionTool(func=audit_label_claims)

# In agents/regulatory_auditor.py

RegulatoryAuditorAgent = LlmAgent(
    name="RegulatoryAuditorAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    instruction="""You are an uncompromising FSSAI Compliance Auditor. Cross-reference label data against Indian food safety laws AND the user's specific health profile.

1. Extract 'nutrients', 'ingredients', 'health_claims', and 'mandatory_warnings' from the LabelExtractorAgent's JSON.
2. BASELINE FSSAI LIMITS: If Saturated Fat > 10g or Sodium > 300mg per 100g, flag this as 'High Risk' (HFSS). 
3. CRITICAL PROFILE OVERRIDES (HARD STOPS):
   - If Profile is "Child (under 12)" OR "Pregnant": Check 'mandatory_warnings' and 'ingredients' for Caffeine, Taurine, or Ginseng. If found, you MUST set overall_status to NON_COMPLIANT and flag it as a SEVERE HEALTH VIOLATION.
   - If Profile is "Diabetic": Check 'total_sugars_g'. If it exceeds 5g per serving, flag as HIGH CONCERN.
4. Output a structured, authoritative FSSAI audit report.""",
    tools=[audit_tool], # Ensure your tool name matches here
)