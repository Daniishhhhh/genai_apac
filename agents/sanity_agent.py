import os, json
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

def enforce_global_truth(audit_json: str) -> dict:
    """
    Final gate: if any high-severity flag exists,
    force overall_status = non_compliant and risk_score >= 80.
    Prevents contradictory compliant/non-compliant coexistence.
    """
    try:
        audit = json.loads(audit_json)
    except Exception as e:
        return {"error": str(e)}

    flags      = audit.get("flags", [])
    high_flags = [f for f in flags if f.get("severity") == "high"]

    if high_flags and audit.get("overall_status") != "non_compliant":
        audit["overall_status"] = "non_compliant"
        audit["risk_score"]     = max(80, audit.get("risk_score", 0))
        audit["sanity_override"] = True
        audit["sanity_reason"]   = (
            f"SanityAgent override: {len(high_flags)} high-severity flag(s) detected. "
            f"Status forced to non_compliant, score floored at 80."
        )
    else:
        audit["sanity_override"] = False

    return audit

sanity_tool = FunctionTool(func=enforce_global_truth)

# In agents/sanity_agent.py

SanityAgent = LlmAgent(
    name="SanityAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash"),
    instruction="""You are a Sanity Checker.
    Your job is to compare the RegulatoryAuditor's flags against the raw data from the LabelExtractorAgent.
    If the LabelExtractor found 'Sugar: 9.4g' and the Auditor says 'Sugar: Unknown', you must OVERRIDE and fix the brand/product names based on the LabelExtractor's data.""",
)