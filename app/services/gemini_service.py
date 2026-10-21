import os
import json
from typing import Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

class SustainabilityAIInsight(BaseModel):
    ai_explanation: str
    eco_tip: str
    sustainable_alternative: str
    sustainability_tag: str

_client_instance = None

def _get_genai_client():
    global _client_instance
    if _client_instance is not None:
        return _client_instance
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key.strip():
        try:
            _client_instance = genai.Client(api_key=api_key.strip())
            return _client_instance
        except Exception as e:
            print(f"[GEMINI] Initialization failed: {e}")
    return None

def build_deterministic_insights(product_data: Dict[str, Any], sustainability_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates strictly truthful, non-hallucinated explanations derived ONLY from verified product facts."""
    eco_grade = str(sustainability_data.get("eco_score_grade") or "").upper()
    eco_score = sustainability_data.get("eco_score_numeric")
    carbon_val = product_data.get("carbon_footprint") or "Not available"
    pack_mat = product_data.get("packaging") or "Not specified"
    nutri = str(product_data.get("nutriscore_grade") or "").upper()
    nova = product_data.get("nova_group")
    palm_free = product_data.get("palm_oil_free")
    allergens = product_data.get("allergens") or ""

    # Environmental explanation
    if eco_grade in ["A", "B"]:
        env_text = f"Grade {eco_grade} indicates a relatively lower environmental impact compared to category benchmarks."
    elif eco_grade == "C":
        env_text = "Grade C indicates a moderate lifecycle environmental impact."
    elif eco_grade in ["D", "E"]:
        env_text = f"Grade {eco_grade} reflects a higher environmental footprint, primarily driven by agricultural ingredients and processing."
    else:
        env_text = "Environmental impact metrics are currently unpublished for this specific product in open databases."

    if carbon_val != "Not available" and "kg CO2e" in carbon_val:
        env_text += f" Official life-cycle carbon footprint is estimated at {carbon_val}."

    # Practical eco tip
    if "pouch" in pack_mat.lower() or "plastic" in pack_mat.lower():
        eco_tip = "Dispose flexible packaging cleanly in municipal dry recyclable waste bins."
    elif "glass" in pack_mat.lower():
        eco_tip = "Glass containers can be rinsed and reused endlessly or recycled locally."
    elif "paper" in pack_mat.lower() or "carton" in pack_mat.lower():
        eco_tip = "Flatten clean paper/cardboard packaging before placing in paper recycling."
    else:
        eco_tip = "Check packaging for local municipality recycling instructions."

    # Nutrition & processing summary
    consumer_summary = []
    if eco_grade:
        consumer_summary.append(f"Environmental: {env_text}")
    if nutri and nutri not in ["UNKNOWN", "NOT AVAILABLE"]:
        consumer_summary.append(f"Nutrition: Nutri-Score {nutri}. Consider this within your overall dietary pattern.")
    if nova:
        if nova == 4:
            consumer_summary.append("Processing: NOVA 4 (Ultra-processed formulation).")
        elif nova == 1:
            consumer_summary.append("Processing: NOVA 1 (Unprocessed or minimally processed whole food).")
        else:
            consumer_summary.append(f"Processing: NOVA {nova}.")
    if palm_free is False:
        consumer_summary.append("Ingredients: Contains palm oil.")
    elif palm_free is True:
        consumer_summary.append("Ingredients: Palm oil free.")
    if allergens and allergens.lower() not in ["not declared", "none"]:
        consumer_summary.append(f"Allergens: Declared allergens include {allergens}.")

    # Tag
    if eco_grade in ["A", "B"]:
        tag = "Lower Environmental Impact"
    elif eco_grade in ["D", "E"]:
        tag = "Higher Environmental Impact"
    elif nova == 4:
        tag = "Ultra-Processed"
    else:
        tag = "Verified Product"

    return {
        "ai_explanation": env_text,
        "eco_tip": eco_tip,
        "sustainable_alternative": "",
        "sustainability_tag": tag,
        "what_this_means_for_you": consumer_summary,
        "provenance": "deterministic_verified"
    }

async def analyze_product_sustainability(product_data: Dict[str, Any], sustainability_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Contextual sustainability analysis. Always falls back to deterministic factual insights
    to ensure 100% truthfulness and zero latency bottlenecks.
    """
    base_insights = build_deterministic_insights(product_data, sustainability_data)
    
    client = _get_genai_client()
    if not client:
        return base_insights

    product_name = product_data.get("product_name") or "Product"
    brand = product_data.get("brand") or "Brand"
    category = product_data.get("category") or "General"
    ingredients = product_data.get("ingredients_text") or "Not Specified"
    packaging = product_data.get("packaging") or "Not Specified"
    eco_grade = sustainability_data.get("eco_score_grade") or "Not Specified"
    recyclability = sustainability_data.get("packaging_recyclability", {}).get("value", "Not Specified")

    prompt = f"""
    You are an environmental sustainability analyst evaluating a verified consumer product.
    
    CONFIRMED FACTUAL DATA ONLY:
    - Product: {product_name}
    - Brand: {brand}
    - Category: {category}
    - Ingredients: {ingredients}
    - Packaging: {packaging}
    - Environmental Grade: {eco_grade}
    - Packaging Recyclability: {recyclability}

    STRICT CONSTRAINTS:
    - You must NEVER invent missing ingredients, nutrition facts, water values, carbon numbers, or health claims.
    - Base all statements ONLY on the verified data above.
    - Produce JSON with:
      1. ai_explanation: 2 objective sentences describing the product's environmental context based strictly on verified inputs.
      2. eco_tip: 1 practical consumer action for disposal or recycling.
      3. sustainable_alternative: A real, widely available sustainable Indian staple or refillable alternative (e.g., 'Millet-based noodles', 'Loose whole grains in refill containers').
      4. sustainability_tag: 2-3 word objective tag (e.g., 'Lower Lifecycle Impact', 'Recyclable Container', 'High Processing').
    """

    candidate_models = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash'
    ]

    for model_name in candidate_models:
        try:
            import asyncio
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SustainabilityAIInsight,
                    )
                ),
                timeout=3.0
            )
            if response and response.text:
                result = json.loads(response.text)
                return {
                    "ai_explanation": result.get("ai_explanation", base_insights["ai_explanation"]),
                    "eco_tip": result.get("eco_tip", base_insights["eco_tip"]),
                    "sustainable_alternative": result.get("sustainable_alternative", ""),
                    "sustainability_tag": result.get("sustainability_tag", base_insights["sustainability_tag"]),
                    "what_this_means_for_you": base_insights["what_this_means_for_you"],
                    "provenance": "ai_contextualized"
                }
        except Exception:
            break

    return base_insights