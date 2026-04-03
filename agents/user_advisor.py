import json
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import os

def format_consumer_report(audit_result_json: str) -> dict:
    try:
        # Clean potential markdown wrappers
        clean_json = audit_result_json.replace("```json", "").replace("```", "").strip()
        audit = json.loads(clean_json[clean_json.find('{'):clean_json.rfind('}')+1])
    except Exception as e:
        return {"error": f"Invalid JSON input: {str(e)}"}

    status = audit.get("overall_status", "needs_review")
    
    # --- SAFE SCORE PARSING ---
    raw_score = audit.get("risk_score", 0)
    try:
        if isinstance(raw_score, str) and not raw_score.isdigit():
            mapping = {"High": 85, "Medium": 45, "Low": 10}
            score = mapping.get(raw_score, 0)
        else:
            score = int(float(raw_score))
    except:
        score = 0

    flags = audit.get("flags", [])
    product = audit.get("product_name", "Unknown Product")
    brand = audit.get("brand", "Unknown Brand")

    # --- SAFE FLAG PARSING (Fixes the AttributeError) ---
    concerns = []
    for f in flags:
        if isinstance(f, dict):
            f_status = f.get("status", "")
            f_severity = f.get("severity", "")
            if f_status == "non_compliant" or f_severity == "high":
                concerns.append({
                    "claim": f.get("claim", "Label Finding"),
                    "issue": f.get("explanation", "Violation of FSSAI standards."),
                    "severity": f_severity
                })
        elif isinstance(f, str):
            # Handle case where flags is just a list of strings
            concerns.append({
                "claim": "General Flag",
                "issue": f,
                "severity": "high" if "high" in f.lower() else "medium"
            })

    # Traffic light logic
    traffic_light, emoji = ("RED", "🚨") if (status == "non_compliant" or score >= 35) else (("GREEN", "✅") if score < 20 else ("AMBER", "⚠️"))

    return {
        "headline": f"{emoji} {product} Audit Results",
        "traffic_light": traffic_light,
        "emoji": emoji,
        "risk_score": score,
        "brand": brand,
        "product_name": product,
        "top_concerns": concerns[:3],
        "plain_summary": f"Audit complete for {product} by {brand}. Score: {score}/100."
    }

format_tool = FunctionTool(func=format_consumer_report)

UserAdvisorAgent = LlmAgent(
    name="UserAdvisorAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash"),
    instruction="Call format_consumer_report with the JSON from the previous turn. Return ONLY the JSON result.",
    tools=[format_tool],
)