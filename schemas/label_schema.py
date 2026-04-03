from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class NutrientData(BaseModel):
    calories_kcal:   Optional[float] = Field(None, description="Energy per 100g in kcal")
    protein_g:       Optional[float] = Field(None, description="Protein per 100g")
    total_carbs_g:   Optional[float] = Field(None, description="Total carbohydrates per 100g")
    total_sugars_g:  Optional[float] = Field(None, description="Total sugars per 100g")
    sodium_mg:       Optional[float] = Field(None, description="Sodium per 100g in mg")
    saturated_fat_g: Optional[float] = Field(None, description="Saturated fat per 100g")
    trans_fat_g:     Optional[float] = Field(None, description="Trans fat per 100g")
    fiber_g:         Optional[float] = Field(None, description="Dietary fibre per 100g")

    @field_validator('trans_fat_g', 'saturated_fat_g', mode='before')
    @classmethod
    def cap_fat(cls, v):
        return None if (v is not None and v > 20) else v

    @field_validator('sodium_mg', mode='before')
    @classmethod
    def cap_sodium(cls, v):
        return None if (v is not None and v > 5000) else v

    @field_validator('calories_kcal', mode='before')
    @classmethod
    def cap_calories(cls, v):
        return None if (v is not None and v > 900) else v


class ExtractedLabel(BaseModel):
    product_name:          str           = Field("Unknown Product", description="Full product name from label")
    brand:                 str           = Field("Unknown Brand",   description="Brand name")
    net_weight:            Optional[str] = Field(None,             description="Net weight/volume")
    health_claims:         List[str]     = Field(default_factory=list, description="All health claims on pack")
    ingredients:           List[str]     = Field(default_factory=list, description="Ingredients list in order")
    nutrients:             NutrientData  = Field(default_factory=NutrientData)
    fssai_license:         Optional[str] = Field(None,             description="FSSAI license number if present")
    extraction_confidence: float         = Field(0.5, ge=0.0, le=1.0, description="Model confidence 0–1")


class ComplianceStatus(str, Enum):
    COMPLIANT     = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW  = "needs_review"


class ComplianceFlag(BaseModel):
    claim:                str
    status:               ComplianceStatus
    regulation_reference: str = ""
    explanation:          str
    severity:             str  # "high" | "medium" | "low"


class ComplianceReport(BaseModel):
    product:        ExtractedLabel
    flags:          List[ComplianceFlag]
    overall_status: ComplianceStatus
    risk_score:     int = Field(..., ge=0, le=100)
    summary:        str
    consumer_advice: str


# ── Phase 3A additions ────────────────────────────────────────────────────────

class ConsumptionVerdict(str, Enum):
    REGULAR    = "Regular"
    OCCASIONAL = "Occasional"
    RARE       = "Rare"


class WellnessReport(BaseModel):
    nutri_score:        str                  # "A" | "B" | "C" | "D" | "E"
    nutri_score_points: int                  # raw numeric score
    consumption_verdict: ConsumptionVerdict
    verdict_reason:     str                  # one-line explanation of verdict
    body_impact:        dict                 # {"benefits": [...], "concerns": [...]}
    daily_comparison:   List[str]            # contextualised RDA sentences
    preservative_flags: List[str]            # INS codes flagged by EducationAgent
    swap_suggestions:   List[dict]           # [{"ingredient": ..., "swap": ..., "risk": ...}]