import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.services.open_food_facts_service import OpenFoodFactsService, ExternalAPITimeoutException
from app.services.sustainability_engine import SustainabilityEngine

class ProductRetrievalService:
    _cached_products: Optional[Dict[str, Any]] = None
    _data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    @classmethod
    def _load_all_datasets(cls) -> Dict[str, Any]:
        if cls._cached_products is not None:
            return cls._cached_products

        merged_data = {}
        if os.path.exists(cls._data_dir):
            for filename in os.listdir(cls._data_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(cls._data_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = json.load(f)
                            if isinstance(content, dict):
                                for k, v in content.items():
                                    merged_data[str(k).strip()] = v
                    except Exception as e:
                        print(f"[ERROR] Loading {filename}: {e}")

        cls._cached_products = merged_data
        print(f"[BACKEND] Loaded {len(cls._cached_products)} verified products in local cache.")
        return cls._cached_products

    @classmethod
    def get_product(cls, barcode: str) -> Optional[Dict[str, Any]]:
        clean_barcode = str(barcode).strip()
        data = cls._load_all_datasets()

        raw_product = None
        source_name = "Local Verified Database"

        # Tier 1: Check Local Verified Cache
        if clean_barcode in data:
            local_product = data[clean_barcode]
            source_name = local_product.get("source", "Local Verified Indian Product")
            raw_product = dict(local_product)
            print(f"[BACKEND] Found barcode '{clean_barcode}' in {source_name}.")

            # If local record lacks Agribalyse LCA data, score, nutriments, or ingredients, query live Open Food Facts v3 for the exact same barcode
            if not local_product.get("ecoscore_data") or local_product.get("ecoscore_score") is None or not local_product.get("nutriments") or not local_product.get("ingredients"):
                try:
                    external_product = OpenFoodFactsService.fetch_by_barcode(clean_barcode)
                    if external_product and external_product.get("barcode") == clean_barcode:
                        if external_product.get("ecoscore_data"):
                            raw_product["ecoscore_data"] = external_product["ecoscore_data"]
                        if external_product.get("ecoscore_score") is not None:
                            raw_product["ecoscore_score"] = external_product["ecoscore_score"]
                        if external_product.get("ecoscore_grade"):
                            raw_product["ecoscore_grade"] = external_product["ecoscore_grade"]
                        if external_product.get("packaging") and not raw_product.get("packaging"):
                            raw_product["packaging"] = external_product["packaging"]
                        if external_product.get("packagings") and not raw_product.get("packagings"):
                            raw_product["packagings"] = external_product["packagings"]
                        if external_product.get("nutriments") and not raw_product.get("nutriments"):
                            raw_product["nutriments"] = external_product["nutriments"]
                        if external_product.get("ingredients") and not raw_product.get("ingredients"):
                            raw_product["ingredients"] = external_product["ingredients"]
                        if external_product.get("nova_group") is not None and raw_product.get("nova_group") is None:
                            raw_product["nova_group"] = external_product["nova_group"]
                        if external_product.get("nutriscore_grade") and not raw_product.get("nutriscore_grade"):
                            raw_product["nutriscore_grade"] = external_product["nutriscore_grade"]
                        if external_product.get("nutriscore_score") is not None and raw_product.get("nutriscore_score") is None:
                            raw_product["nutriscore_score"] = external_product["nutriscore_score"]
                        if external_product.get("allergens") and not raw_product.get("allergens"):
                            raw_product["allergens"] = external_product["allergens"]
                        if external_product.get("allergens_tags") and not raw_product.get("allergens_tags"):
                            raw_product["allergens_tags"] = external_product["allergens_tags"]
                        if external_product.get("additives_tags") and not raw_product.get("additives_tags"):
                            raw_product["additives_tags"] = external_product["additives_tags"]
                        if external_product.get("ingredients_analysis_tags") and not raw_product.get("ingredients_analysis_tags"):
                            raw_product["ingredients_analysis_tags"] = external_product["ingredients_analysis_tags"]
                except Exception as e:
                    print(f"[BACKEND] Live enrichment skipped for {clean_barcode}: {e}")
        else:
            # Tier 2: Search Live External Sources (Open Food Facts / Open Beauty Facts)
            print(f"[BACKEND] Barcode '{clean_barcode}' not in local database. Querying Open Food Facts API...")
            try:
                external_product = OpenFoodFactsService.fetch_by_barcode(clean_barcode)
                if external_product:
                    raw_product = external_product
                    source_name = external_product.get("source", "Open Food Facts API")
                    cls._cached_products[clean_barcode] = raw_product
            except ExternalAPITimeoutException:
                raise
            except Exception as e:
                print(f"[BACKEND ERROR] External lookup failed for {clean_barcode}: {e}")

        if not raw_product:
            return None

        # Build standardized Product record without inventing missing values
        clean_name = str(raw_product.get("product_name") or "").strip()
        clean_brand = str(raw_product.get("brand") or raw_product.get("brands") or "").strip()
        clean_category = str(raw_product.get("category") or raw_product.get("categories") or "").strip()
        clean_ingredients_text = str(raw_product.get("ingredients_text") or "").strip()
        raw_packaging = str(raw_product.get("packaging") or raw_product.get("packaging_text") or "").strip()
        clean_packaging = raw_packaging if SustainabilityEngine.is_valid_packaging(raw_packaging) else ""

        # Calculate authentic sustainability metrics via engine
        sustainability = SustainabilityEngine.evaluate(raw_product)

        carb_metric = sustainability.get("carbon_footprint", {})
        water_metric = sustainability.get("water_usage", {})
        pack_metric = sustainability.get("packaging_recyclability", {})

        # Extract structured nutrition facts
        raw_nutriments = raw_product.get("nutriments") or {}
        nutriments_clean = cls._format_nutriments(raw_nutriments)

        # Extract structured ingredients hierarchy
        ingredients_list = raw_product.get("ingredients") or []
        allergens_text = str(raw_product.get("allergens") or "").strip()
        allergens_tags = raw_product.get("allergens_tags") or []
        additives_tags = raw_product.get("additives_tags") or []

        retrieved_at = datetime.now(timezone.utc).isoformat()

        product_payload = {
            "barcode": clean_barcode,
            "product_name": clean_name if clean_name else "Not available",
            "brand": clean_brand if clean_brand else "Not available",
            "category": clean_category if clean_category else "Not available",
            "quantity": str(raw_product.get("quantity") or "").strip(),
            "serving_size": str(raw_product.get("serving_size") or "").strip(),
            "image_url": str(raw_product.get("image_url") or "").strip(),
            "ingredients_text": clean_ingredients_text if clean_ingredients_text else "Not available",
            "ingredients": ingredients_list,
            "allergens": allergens_text if allergens_text else "Not declared",
            "allergens_tags": allergens_tags,
            "additives_tags": additives_tags,
            "palm_oil_free": sustainability.get("palm_oil_free"),
            "vegan": sustainability.get("vegan"),
            "vegetarian": sustainability.get("vegetarian"),
            "packaging": clean_packaging if clean_packaging else "Not available",
            
            # Environmental Score fields
            "eco_score_grade": sustainability.get("eco_score_grade"),
            "eco_score": sustainability.get("eco_score_numeric"),
            "eco_score_provenance": sustainability.get("eco_score_provenance"),
            "eco_score_provenance_label": sustainability.get("eco_score_provenance_label"),
            "eco_score_explanation": sustainability.get("eco_score_explanation"),
            
            # Carbon Footprint
            "carbon_footprint": carb_metric.get("value", "Not available"),
            "carbon_footprint_status": carb_metric.get("status", "unavailable"),
            "carbon_footprint_label": carb_metric.get("provenance_label", "Unavailable"),
            "carbon_footprint_explanation": carb_metric.get("methodology", "Carbon footprint unavailable."),
            
            # Water Impact
            "water_usage": water_metric.get("value", "Product-specific water impact unavailable"),
            "water_usage_status": water_metric.get("status", "unavailable"),
            "water_usage_label": water_metric.get("provenance_label", "Unavailable"),
            "water_usage_explanation": water_metric.get("methodology", "Water impact unavailable."),
            
            # Packaging Recyclability
            "packaging_recyclability": pack_metric.get("value", "Not available"),
            "packaging_status": pack_metric.get("status", "unavailable"),
            "packaging_label": pack_metric.get("provenance_label", "Unavailable"),
            "packaging_explanation": pack_metric.get("methodology", "Packaging composition not declared."),
            
            # Nutrition profile
            "nutriscore_grade": sustainability.get("nutriscore_grade") or "Not available",
            "nutriscore_score": sustainability.get("nutriscore_score"),
            "nova_group": sustainability.get("nova_group"),
            "nutriments": nutriments_clean,
            
            # Metadata & Provenance
            "source": source_name,
            "countries": raw_product.get("countries", []),
            "retrieved_at": retrieved_at,
        }

        # Sections for clean structured contract
        environment_section = {
            "grade": sustainability.get("eco_score_grade"),
            "score": sustainability.get("eco_score_numeric"),
            "provenance": sustainability.get("eco_score_provenance"),
            "provenance_label": sustainability.get("eco_score_provenance_label"),
            "explanation": sustainability.get("eco_score_explanation"),
            "carbon": carb_metric,
            "water": water_metric,
            "packaging": pack_metric,
        }

        nutrition_section = {
            "nutriscore_grade": sustainability.get("nutriscore_grade"),
            "nutriscore_score": sustainability.get("nutriscore_score"),
            "nova_group": sustainability.get("nova_group"),
            "nutriments": nutriments_clean,
        }

        ingredients_section = {
            "text": clean_ingredients_text if clean_ingredients_text else "Not available",
            "items": ingredients_list,
            "allergens": allergens_text,
            "allergens_tags": allergens_tags,
            "additives_tags": additives_tags,
            "palm_oil_free": sustainability.get("palm_oil_free"),
            "vegan": sustainability.get("vegan"),
            "vegetarian": sustainability.get("vegetarian"),
        }

        packaging_section = {
            "declared": clean_packaging if clean_packaging else "Not available",
            "recyclability": pack_metric.get("value"),
            "recyclability_status": pack_metric.get("status"),
            "recyclability_label": pack_metric.get("provenance_label"),
        }

        provenance_section = {
            "product_identity": "DIRECT PRODUCT DATA",
            "eco_score": sustainability.get("eco_score_provenance_label"),
            "carbon": carb_metric.get("provenance_label"),
            "water": water_metric.get("provenance_label"),
            "packaging": pack_metric.get("provenance_label"),
            "source": source_name,
            "retrieved_at": retrieved_at,
        }

        return {
            "source": source_name,
            "barcode": clean_barcode,
            "product": product_payload,
            "environment": environment_section,
            "nutrition": nutrition_section,
            "ingredients": ingredients_section,
            "packaging": packaging_section,
            "provenance": provenance_section,
            "raw_sustainability": sustainability
        }

    @classmethod
    def _format_nutriments(cls, nutriments: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts and formats key nutrients cleanly per 100g and per serving."""
        keys = [
            ("energy_kcal", ["energy-kcal_100g", "energy-kcal", "energy_100g"], "kcal"),
            ("energy_kj", ["energy-kj_100g", "energy-kj"], "kJ"),
            ("fat", ["fat_100g", "fat"], "g"),
            ("saturated_fat", ["saturated-fat_100g", "saturated-fat"], "g"),
            ("carbohydrates", ["carbohydrates_100g", "carbohydrates"], "g"),
            ("sugars", ["sugars_100g", "sugars"], "g"),
            ("fiber", ["fiber_100g", "fiber"], "g"),
            ("proteins", ["proteins_100g", "proteins"], "g"),
            ("salt", ["salt_100g", "salt"], "g"),
            ("sodium", ["sodium_100g", "sodium"], "g"),
        ]

        formatted = {}
        for out_key, candidates, unit in keys:
            val = None
            for cand in candidates:
                if cand in nutriments and nutriments[cand] is not None:
                    try:
                        val = round(float(nutriments[cand]), 2)
                        break
                    except (ValueError, TypeError):
                        pass
            
            serving_cand = out_key.replace("_", "-") + "_serving"
            serving_val = None
            if serving_cand in nutriments and nutriments[serving_cand] is not None:
                try:
                    serving_val = round(float(nutriments[serving_cand]), 2)
                except (ValueError, TypeError):
                    pass

            formatted[out_key] = {
                "per_100g": val,
                "per_serving": serving_val,
                "unit": unit
            }
        return formatted

    @classmethod
    def get_featured_products(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns sample verified products for initial display in the app."""
        data = cls._load_all_datasets()
        results = []
        for barcode in list(data.keys())[:limit]:
            prod_record = cls.get_product(barcode)
            if prod_record:
                results.append(prod_record["product"])
        return results