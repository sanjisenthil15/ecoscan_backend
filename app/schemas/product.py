from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class MetricProvenance(BaseModel):
    value: Optional[str] = None
    status: str = Field(description="'direct_source', 'official_calculated', 'category_baseline', 'methodology_calculated', or 'unavailable'")
    provenance_label: Optional[str] = Field(None, description="Human readable transparency label")
    methodology: Optional[str] = Field(None, description="Transparency explanation of source")

class SustainabilityDetails(BaseModel):
    eco_score_grade: Optional[str] = Field(None, description="Official Eco-Score grade A to E or None")
    eco_score_numeric: Optional[int] = Field(None, description="Score from 0 to 100")
    eco_score_provenance: Optional[str] = None
    eco_score_provenance_label: Optional[str] = None
    eco_score_explanation: Optional[str] = None
    carbon_footprint: MetricProvenance
    water_usage: MetricProvenance
    packaging_recyclability: MetricProvenance
    palm_oil_free: Optional[bool] = None
    vegan: Optional[bool] = None
    vegetarian: Optional[bool] = None
    nova_group: Optional[int] = Field(None, description="NOVA food processing group (1-4)")
    nutriscore_grade: Optional[str] = None
    nutriscore_score: Optional[int] = None
    ai_explanation: Optional[str] = None
    eco_tip: Optional[str] = None
    sustainable_alternative: Optional[str] = None
    what_this_means_for_you: List[str] = []

class ProductSchema(BaseModel):
    barcode: str
    product_name: str
    brand: str
    category: str
    packaging: str
    ingredients_text: str
    ingredients: List[Dict[str, Any]] = []
    allergens: str = ""
    allergens_tags: List[str] = []
    additives_tags: List[str] = []
    nutriments: Dict[str, Any] = {}
    image_url: str
    countries: List[str] = []
    source: str
    retrieved_at: Optional[str] = None

class ProductLookupResponse(BaseModel):
    success: bool
    status: str = "success"
    barcode: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    product: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, Any]] = None
    nutrition: Optional[Dict[str, Any]] = None
    ingredients: Optional[Dict[str, Any]] = None
    packaging: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
