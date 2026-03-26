import json
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import os


def format_consumer_report(audit_result_json: str) -> dict:
    """
    Converts technical compliance audit into a consumer-friendly summary.
    Traffic light system: GREEN / AMBER / RED
    Designed for <3 second comprehension.
    """
    try:
        audit = json.loads(audit_result_json)
    except Exception as e:
        return {"error": f"Invalid JSON: {e}"}

    status  = audit.get("overall_status", "needs_review")
    score   = audit.get("risk_score", 0)
    flags   = audit.get("flags", [])
    product = audit.get("product_name", "This product")
    brand   = audit.get("brand", "")

    # Traffic light
    if status == "compliant" and score < 20:
        traffic_light = "GREEN"
        headline      = f"{product} by {brand} passes FSSAI compliance checks."
        emoji         = "✅"
    elif status == "non_compliant" or score >= 35:
        traffic_light = "RED"
        headline      = f"⚠️ {product} by {brand} has misleading health claims."
        emoji         = "🚨"
    else:
        traffic_light = "AMBER"
        headline      = f"{product} by {brand} has some claims that need verification."
        emoji         = "⚠️"

    # Top concerns in plain English
    concerns = []
    for f in flags:
        if f["status"] == "non_compliant":
            concerns.append({
                "claim": f["claim"],
                "issue": f["explanation"],
                "severity": f["severity"]
            })

    # Plain English summary (max 2 sentences)
    if not concerns:
        plain_summary = (
            f"{product} appears to comply with FSSAI nutritional claim regulations. "
            f"All {audit.get('total_claims_checked', 0)} health claims checked."
        )
    else:
        worst = concerns[0]
        plain_summary = (
            f"Found {len(concerns)} misleading claim(s). "
            f"Key issue: {worst['issue'][:150]}"
        )

    return {
        "headline": headline,
        "traffic_light": traffic_light,
        "emoji": emoji,
        "risk_score": score,
        "plain_summary": plain_summary,
        "top_concerns": concerns[:3],  # max 3 for mobile UI
        "total_claims_checked": audit.get("total_claims_checked", 0),
        "product_name": product,
        "brand": brand,
        "disclaimer": (
            "NutriGuard audits labels for FSSAI regulatory compliance only. "
            "For personal dietary advice, consult a registered dietitian."
        )
    }

format_tool = FunctionTool(func=format_consumer_report)

UserAdvisorAgent = LlmAgent(
    name="UserAdvisorAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Translates compliance findings into consumer-friendly summaries.",
    instruction="""You are a Consumer Advocate.
You receive a JSON string of compliance audit results.
Call format_consumer_report with that JSON.
Return the formatted report.
NEVER provide medical advice. NEVER suggest dietary changes for health conditions.
Your job is ONLY to present regulatory findings in plain language.""",
    tools=[format_tool],
)
