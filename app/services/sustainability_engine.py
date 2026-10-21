from typing import Dict, Any, Optional, List
import re

class SustainabilityEngine:
    """
    Evaluates sustainability transparently with strict data provenance:
    - DIRECT_PRODUCT: Exact product-specific measured data
    - OFFICIAL_CALCULATED: Official calculated Agribalyse LCA value
    - CATEGORY_LCA_BASELINE: Category-level lifecycle benchmark (with clear disclaimer)
    - UNAVAILABLE: Truthfully declared when reliable data is missing
    """

    # Packaging regex to filter out date stamps, batch/lot codes, and non-packaging noise
    DATE_OR_NON_PACKAGING_PATTERN = re.compile(
        r'(?:'
        r'\b(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\b'
        r'|\b\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s*(?:\d{2,4})?\b'
        r'|\b20\d{2}\b|\b19\d{2}\b'
        r'|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b'
        r'|\b(?:mfg|mfd|exp|expiry|batch|pkd|packed|best before|use by|lot|bbd)\b'
        r')',
        re.IGNORECASE
    )

    HIGH_RECYCLABILITY_TERMS = [
        "glass", "verre", "bocal", "paper", "paperboard", "cardboard", "carton",
        "aluminium", "aluminum", "tin", "metal", "steel", "can", "tetra pak", "tetrapak"
    ]

    MODERATE_RECYCLABILITY_TERMS = [
        "pet", "hdpe", "ldpe", "polypropylene", "pp", "mono-layer", "monolayer",
        "plastic", "plastique", "kunststoff", "bouteille", "bottle", "tub", "tray",
        "pouch", "sachet", "box", "boîte", "pot", "wrap"
    ]

    LOW_RECYCLABILITY_TERMS = [
        "multi-layer", "metallized", "multilayer", "foil packet", "bopp", "bopp/pe",
        "composites", "7 other", "other plastic"
    ]

    @classmethod
    def is_valid_packaging(cls, packaging_text: Optional[str]) -> bool:
        if not packaging_text:
            return False
        cleaned = str(packaging_text).strip().lower()
        if cleaned in ["", "not available", "not specified", "packaging details not specified", "unknown packaging", "unknown"]:
            return False
        if cls.DATE_OR_NON_PACKAGING_PATTERN.search(cleaned):
            return False
        all_terms = cls.HIGH_RECYCLABILITY_TERMS + cls.MODERATE_RECYCLABILITY_TERMS + cls.LOW_RECYCLABILITY_TERMS
        return any(term in cleaned for term in all_terms)

    @classmethod
    def evaluate(cls, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        # ==============================================================
        # 1. Environmental Score / Eco-Score (Authentic preservation - NO arbitrary score fabrication)
        # ==============================================================
        ecoscore_data = raw_product.get("ecoscore_data") or {}
        raw_eco_score = (
            raw_product.get("ecoscore_score")
            or raw_product.get("eco_score_numeric")
            or raw_product.get("eco_score")
            or ecoscore_data.get("score")
        )
        eco_grade = (
            raw_product.get("ecoscore_grade")
            or raw_product.get("eco_score_grade")
            or ecoscore_data.get("grade")
        )

        eco_score_num: Optional[int] = None
        eco_provenance: str = "unavailable"
        eco_provenance_label: str = "Unavailable"
        eco_explanation: str = "Environmental score not available for this exact product in current trusted registries."

        # Clean grade
        clean_grade: Optional[str] = None
        if eco_grade and str(eco_grade).strip().lower() in ["a", "b", "c", "d", "e"]:
            clean_grade = str(eco_grade).strip().lower()

        # Strict numeric score: ONLY accept officially provided integer score
        if raw_eco_score is not None:
            try:
                parsed_val = int(raw_eco_score)
                if 0 <= parsed_val <= 100:
                    eco_score_num = parsed_val
            except (ValueError, TypeError):
                eco_score_num = None

        if clean_grade and eco_score_num is not None:
            eco_provenance = "official_calculated"
            eco_provenance_label = "Official calculated value"
            eco_explanation = f"Officially calculated Environmental Score ({eco_score_num}/100, Grade {clean_grade.upper()}) based on verified Agribalyse life cycle assessment (LCA) and product ingredients."
        elif clean_grade and eco_score_num is None:
            # ONLY grade is published, DO NOT invent a numeric score!
            eco_provenance = "official_grade_only"
            eco_provenance_label = "Official Grade (Score not published)"
            eco_explanation = f"Official Environmental Grade {clean_grade.upper()} provided by Open Food Facts. Numerical sub-score is not published for this SKU."
        elif not clean_grade and eco_score_num is not None:
            eco_provenance = "official_calculated"
            eco_provenance_label = "Official calculated value"
            eco_explanation = f"Officially calculated Environmental Score ({eco_score_num}/100) based on verified Agribalyse LCA."
            # Assign official standard grade bucket strictly as display helper if official score exists
            if eco_score_num >= 80:
                clean_grade = "a"
            elif eco_score_num >= 65:
                clean_grade = "b"
            elif eco_score_num >= 50:
                clean_grade = "c"
            elif eco_score_num >= 35:
                clean_grade = "d"
            else:
                clean_grade = "e"
        else:
            clean_grade = None
            eco_score_num = None
            eco_provenance = "unavailable"
            eco_provenance_label = "Unavailable"
            eco_explanation = "Environmental score is not available for this exact product in public databases."

        # ==============================================================
        # 2. Packaging Recyclability Evaluation
        # ==============================================================
        packaging_text = (
            raw_product.get("packaging")
            or raw_product.get("packaging_text")
            or ""
        )
        pack_lower = str(packaging_text).strip().lower()

        # Check if packagings list provides packaging materials
        if (not pack_lower or not cls.is_valid_packaging(pack_lower)) and isinstance(raw_product.get("packagings"), list):
            pack_list = raw_product["packagings"]
            materials = []
            for p_item in pack_list:
                if isinstance(p_item, dict):
                    m = p_item.get("material", {})
                    if isinstance(m, dict) and m.get("id"):
                        materials.append(m["id"].replace("en:", "").replace("-", " "))
                    elif isinstance(m, str) and m:
                        materials.append(m.replace("en:", "").replace("-", " "))
            if materials:
                candidate_text = ", ".join(materials)
                if cls.is_valid_packaging(candidate_text):
                    pack_lower = candidate_text.lower()
                    packaging_text = candidate_text.title()

        if not cls.is_valid_packaging(pack_lower):
            recyclability = {
                "value": "Not available",
                "status": "unavailable",
                "provenance_label": "Unavailable",
                "methodology": "Packaging material specification is not declared on packaging or database."
            }
        elif any(term in pack_lower for term in cls.HIGH_RECYCLABILITY_TERMS):
            recyclability = {
                "value": "High (Widely Recyclable Material)",
                "status": "methodology_calculated",
                "provenance_label": "Material classification",
                "methodology": "Material classification based on declared packaging material (Paper/Glass/Metal)."
            }
        elif any(term in pack_lower for term in cls.MODERATE_RECYCLABILITY_TERMS):
            recyclability = {
                "value": "Moderate (Check local municipality facilities for polymers)",
                "status": "methodology_calculated",
                "provenance_label": "Material classification",
                "methodology": "Material classification from declared polymer packaging (PET/HDPE/PP)."
            }
        elif any(term in pack_lower for term in cls.LOW_RECYCLABILITY_TERMS):
            recyclability = {
                "value": "Low (Multi-layer / Metallized laminate not easily recycled)",
                "status": "methodology_calculated",
                "provenance_label": "Material classification",
                "methodology": "Material classification from multi-layer composite plastic declaration."
            }
        else:
            recyclability = {
                "value": "Not available",
                "status": "unavailable",
                "provenance_label": "Unavailable",
                "methodology": "Packaging material specification is not declared on packaging or database."
            }

        # ==============================================================
        # 3. Palm Oil, Vegan, and Vegetarian Analysis
        # ==============================================================
        ingredients_text = str(raw_product.get("ingredients_text") or "").strip()
        analysis_tags = raw_product.get("ingredients_analysis_tags") or []
        
        # Palm oil check
        palm_oil_free: Optional[bool] = None
        if "en:palm-oil" in analysis_tags:
            palm_oil_free = False
        elif "en:palm-oil-free" in analysis_tags:
            palm_oil_free = True
        elif ingredients_text and ingredients_text.lower() not in ["not available", "none"]:
            palm_oil_free = not ("palm" in ingredients_text.lower())

        # Vegan check
        vegan: Optional[bool] = None
        if "en:vegan" in analysis_tags:
            vegan = True
        elif "en:non-vegan" in analysis_tags:
            vegan = False

        # Vegetarian check
        vegetarian: Optional[bool] = None
        if "en:vegetarian" in analysis_tags:
            vegetarian = True
        elif "en:non-vegetarian" in analysis_tags:
            vegetarian = False

        # ==============================================================
        # 4. Carbon Footprint (Strict Source Provenance - NO FAKE NUMBERS)
        # ==============================================================
        agribalyse = ecoscore_data.get("agribalyse") or {}
        co2_total = agribalyse.get("co2_total")

        if co2_total is not None:
            try:
                co2_val = float(co2_total)
                carbon_metric = {
                    "value": f"{co2_val:.2f} kg CO2e/kg",
                    "unit": "kg CO2e/kg",
                    "type": "OFFICIAL_CALCULATED",
                    "status": "official_calculated",
                    "provenance_label": "Official calculated value",
                    "methodology": "Official Agribalyse life cycle assessment reference. Evaluates raw agricultural ingredients, processing, transport, and packaging.",
                    "confidence": "high",
                    "source": "ADEME Agribalyse / Open Food Facts"
                }
            except (ValueError, TypeError):
                carbon_metric = {
                    "value": f"{co2_total} kg CO2e/kg",
                    "unit": "kg CO2e/kg",
                    "type": "OFFICIAL_CALCULATED",
                    "status": "official_calculated",
                    "provenance_label": "Official calculated value",
                    "methodology": "Official Agribalyse LCA reference. Evaluates lifecycle carbon impact based on verified inputs.",
                    "confidence": "high",
                    "source": "ADEME Agribalyse / Open Food Facts"
                }
        else:
            carbon_metric = {
                "value": "Not available",
                "unit": "",
                "type": "UNAVAILABLE",
                "status": "unavailable",
                "provenance_label": "Unavailable",
                "methodology": "Product-specific carbon footprint unavailable in current trusted registries.",
                "confidence": "unavailable",
                "source": "Unavailable"
            }

        # ==============================================================
        # 5. Water Impact (DO NOT INVENT 350, 450, 500, 5500 L!)
        # ==============================================================
        raw_water = raw_product.get("water_usage") or raw_product.get("water_footprint")
        if raw_water and str(raw_water).strip().lower() not in ["", "not available", "none", "null"]:
            water_metric = {
                "value": str(raw_water).strip(),
                "unit": "L/kg",
                "type": "DIRECT_PRODUCT",
                "status": "direct_source",
                "provenance_label": "Product-specific",
                "methodology": "Product-specific measured water impact from verified registry.",
                "confidence": "high",
                "source": "Verified Product Registry"
            }
        else:
            water_metric = {
                "value": "Product-specific water impact unavailable",
                "unit": "",
                "type": "UNAVAILABLE",
                "status": "unavailable",
                "provenance_label": "Unavailable",
                "methodology": "Direct product manufacturing water consumption is not declared on consumer packaging or public food life-cycle databases.",
                "confidence": "unavailable",
                "source": "Unavailable"
            }

        # ==============================================================
        # 6. Nutri-Score & NOVA
        # ==============================================================
        nutri = raw_product.get("nutriscore_grade") or raw_product.get("nutrition_grade")
        if nutri and str(nutri).strip().lower() in ["a", "b", "c", "d", "e"]:
            nutriscore_grade = str(nutri).strip().upper()
        else:
            nutriscore_grade = None

        nova = raw_product.get("nova_group")
        try:
            nova_group = int(nova) if nova is not None and int(nova) in [1, 2, 3, 4] else None
        except (ValueError, TypeError):
            nova_group = None

        return {
            "eco_score_grade": clean_grade,
            "eco_score_numeric": eco_score_num,
            "eco_score_provenance": eco_provenance,
            "eco_score_provenance_label": eco_provenance_label,
            "eco_score_explanation": eco_explanation,
            "carbon_footprint": carbon_metric,
            "water_usage": water_metric,
            "packaging_recyclability": recyclability,
            "palm_oil_free": palm_oil_free,
            "vegan": vegan,
            "vegetarian": vegetarian,
            "nutriscore_grade": nutriscore_grade,
            "nova_group": nova_group
        }
