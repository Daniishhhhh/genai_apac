import os
from typing import Optional, List # Ensure Optional is here
import json
from pydantic import BaseModel
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from schemas.label_schema import ExtractedLabel
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
import base64

vertexai.init(project=os.environ["PROJECT_ID"], location="us-central1")

# ---- Vision Tool ----
def extract_label_from_image(image_path: str) -> dict:
    """
    Takes a local image path or GCS URI.
    Returns structured nutrient JSON from Gemini Vision.
    """
    model = GenerativeModel("gemini-2.5-flash")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    image_part = Part.from_data(
        data=base64.b64decode(image_data),
        mime_type="image/jpeg"
    )

    prompt = """You are a Vision Specialist auditing Indian packaged food labels.

Carefully analyze this food label image. Extract ALL visible information.

CRITICAL: If the label is on curved packaging or has small fonts, 
use your best estimate but lower the extraction_confidence score accordingly.

Return ONLY a valid JSON object matching this exact schema — no markdown, no explanation:
{
  "product_name": "string",
  "brand": "string", 
  "net_weight": "string or null",
  "health_claims": ["list of all health/nutrition claims visible on pack"],
  "ingredients": ["ingredient1", "ingredient2", "...in order as printed"],
  "nutrients": {
    "total_sugars_g": number or null,
    "sodium_mg": number or null,
    "saturated_fat_g": number or null,
    "trans_fat_g": number or null,
    "total_carbs_g": number or null,
    "protein_g": number or null,
    "calories_kcal": number or null
  },
  "fssai_license": "string or null",
  "extraction_confidence": 0.0 to 1.0
}"""

    response = model.generate_content([image_part, prompt])
    raw_json = response.text.strip()

    # Strip markdown code fences if model adds them
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    # Validate with Pydantic
    parsed = ExtractedLabel(**json.loads(raw_json))
    return parsed.model_dump()

extract_label_tool = FunctionTool(func=extract_label_from_image)

# ---- ADK Agent ----
LabelExtractorAgent = LlmAgent(
    name="LabelExtractorAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Extracts structured nutritional data from food label images.",
    instruction="""You are a Vision Specialist. 
Your sole job is to call the extract_label_from_image tool with the provided image path
and return the structured JSON result. Do not add commentary.
If confidence is below 0.6, flag this in your response.""",
    tools=[extract_label_tool],
)