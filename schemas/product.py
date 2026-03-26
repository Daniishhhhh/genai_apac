from pydantic import BaseModel, Field
from typing import List, Optional

class ProductLabel(BaseModel):
    product_name: str = Field(description="The name of the food product")
    brand: str = Field(description="The brand manufacturer")
    sugars_g: float = Field(description="Total sugars per 100g/ml")
    sodium_mg: float = Field(description="Sodium content per 100g/ml")
    saturated_fat_g: float = Field(description="Saturated fat per 100g/ml")
    ingredients: List[str] = Field(description="List of ingredients found on the label")
    claims: List[str] = Field(description="Marketing claims like 'Sugar Free' or 'Low Sodium'")