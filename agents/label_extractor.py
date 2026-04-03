import os
import json
import mimetypes
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.genai import Client, types

# --- Tool Function ---
def extract_label_from_image(image_path: str) -> dict:
    """
    Directly calls the Gemini API to extract JSON from a food label image with strict schema.
    """
    client = Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model_id = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")

    if not os.path.exists(image_path):
        return {"error": f"Image not found at {image_path}"}

    # Detect mime type (png vs jpg)
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # CRITICAL: We define the schema here to enforce the keys exactly
    schema = {
        "type": "OBJECT",
        "properties": {
            "product_name": {"type": "STRING"},
            "brand": {"type": "STRING"},
            "net_weight": {"type": "STRING"},
            "health_claims": {"type": "ARRAY", "items": {"type": "STRING"}},
            "ingredients": {"type": "ARRAY", "items": {"type": "STRING"}},
            "mandatory_warnings": {"type": "ARRAY", "items": {"type": "STRING"}},
            "nutrients": {
                "type": "OBJECT",
                "properties": {
                    "total_sugars_g": {"type": "NUMBER"},
                    "sodium_mg": {"type": "NUMBER"},
                    "saturated_fat_g": {"type": "NUMBER"},
                    "trans_fat_g": {"type": "NUMBER"},
                    "total_carbs_g": {"type": "NUMBER"},
                    "protein_g": {"type": "NUMBER"},
                    "calories_kcal": {"type": "NUMBER"},
                    "fiber_g": {"type": "NUMBER"}
                },
                "required": ["total_sugars_g", "sodium_mg", "saturated_fat_g", "calories_kcal"]
            },
            "fssai_license": {"type": "STRING"},
            "extraction_confidence": {"type": "NUMBER"}
        },
        "required": ["product_name", "nutrients", "ingredients"]
    }

    prompt = """Analyze this Indian food label image. Extract values into the provided JSON schema. 
    If a nutrient value is missing, use 0. Ensure all nutrient keys exist."""

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema, # Forces the AI to use your specific keys
                temperature=0.1
            )
        )
        
        return response.parsed # Directly returns the validated dictionary

    except Exception as e:
        return {
            "error": f"Extraction failed: {str(e)}", 
            "nutrients": {
                "calories_kcal": 0, "total_sugars_g": 0, "sodium_mg": 0, "saturated_fat_g": 0
            },
            "extraction_confidence": 0.0
        }

# --- Agent Definition ---
extract_label_tool = FunctionTool(func=extract_label_from_image)

LabelExtractorAgent = LlmAgent(
    name="LabelExtractorAgent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Extracts structured nutritional data from food label images.",
    instruction="""You are a highly advanced Vision AI and FSSAI Data Extractor. Your job is to read food packaging labels, even if the photo is angled, blurry, or partial.

1. Call the extract_label_from_image tool with the provided image_path.
2. INFER MISSING DATA: Scan the image for the Product Name and Brand. If they aren't explicitly labeled, infer the Brand from the largest logos (e.g., "Haldiram's", "Cavin's", "Sting") and the Product Name from the main text. Do NOT default to "Unknown" if you can reasonably read the package.
3. EXTRACT THE NUTRITION TABLE & INGREDIENTS. If an exact number is cut off, use null.
4. CRITICAL FSSAI WARNING SCAN: You MUST scan for any fine-print warnings (e.g., "Contains Caffeine", "Not recommended for children", "Contains Artificial Sweetener"). Add these exact phrases into the "mandatory_warnings" JSON array.
5. You MUST RETURN ONLY THE RAW JSON. No conversational text. Wrap your output in ```json blocks.""",
    tools=[extract_label_tool],
)