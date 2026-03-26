from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class NutrientData(BaseModel):
    calories_kcal:    Optional[float] = None
    protein_g:        Optional[float] = None
    total_carbs_g:    Optional[float] = None
    total_sugars_g:   Optional[float] = None
    sodium_mg:        Optional[float] = None
    saturated_fat_g:  Optional[float] = None
    trans_fat_g:      Optional[float] = None

    @field_validator('trans_fat_g', 'saturated_fat_g', mode='before')
    @classmethod
    def cap_fat(cls, v):
        return None if (v is not None and v > 20) else v

    @field_validator('sodium_mg', mode='before')
    @classmethod
    def cap_sodium(cls, v):
        return None if (v is not None and v > 5000) else v

class ExtractedLabel(BaseModel):
    product_name:          str            = "Unknown Product"
    brand:                 str            = "Unknown Brand"
    net_weight:            Optional[str]  = None
    health_claims:         List[str]      = []
    ingredients:           List[str]      = []
    nutrients:             NutrientData   = NutrientData()
    fssai_license:         Optional[str]  = None
    extraction_confidence: float          = 0.5

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"

class NutrientData(BaseModel):
    total_sugars_g: Optional[float] = Field(None, description="Total sugars per 100g")
    sodium_mg: Optional[float] = Field(None, description="Sodium per 100g in mg")
    saturated_fat_g: Optional[float] = Field(None, description="Saturated fat per 100g")
    trans_fat_g: Optional[float] = Field(None, description="Trans fat per 100g")
    total_carbs_g: Optional[float] = Field(None, description="Total carbohydrates per 100g")
    protein_g: Optional[float] = Field(None, description="Protein per 100g")
    calories_kcal: Optional[float] = Field(None, description="Energy per 100g in kcal")

class ExtractedLabel(BaseModel):
    product_name: str = Field(..., description="Full product name from label")
    brand: str = Field(..., description="Brand name")
    net_weight: Optional[str] = Field(None, description="Net weight/volume")
    health_claims: List[str] = Field(default_factory=list, description="All health claims on pack")
    ingredients: List[str] = Field(default_factory=list, description="Ingredients list in order")
    nutrients: NutrientData
    fssai_license: Optional[str] = Field(None, description="FSSAI license number if present")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence 0-1")

class ComplianceFlag(BaseModel):
    claim: str
    status: ComplianceStatus
    regulation_reference: str
    explanation: str
    severity: str  # "high", "medium", "low"

class ComplianceReport(BaseModel):
    product: ExtractedLabel
    flags: List[ComplianceFlag]
    overall_status: ComplianceStatus
    risk_score: int = Field(..., ge=0, le=100, description="0=safe, 100=highly non-compliant")
    summary: str
    consumer_advice: str
from pydantic import field_validator

class NutrientDataValidated(NutrientData):
    """NutrientData with sanity-check validators."""

    @field_validator('trans_fat_g', 'saturated_fat_g', mode='before')
    @classmethod
    def cap_fat(cls, v):
        if v is not None and v > 20:
            return None   # discard physically impossible value
        return v

    @field_validator('sodium_mg', mode='before')
    @classmethod
    def cap_sodium(cls, v):
        if v is not None and v > 5000:
            return None
        return v

    @field_validator('calories_kcal', mode='before')
    @classmethod
    def cap_calories(cls, v):
        if v is not None and v > 900:
            return None
        return v
