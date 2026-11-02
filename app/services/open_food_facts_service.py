import requests
from typing import Optional, Dict, Any, List

class ExternalAPITimeoutException(Exception):
    """Raised when external food/beauty registry requests time out."""
    pass

class OpenFoodFactsService:
    """
    Service to fetch live, authentic product records from Open Food Facts (API v3 & v2) & Open Beauty Facts.
    """
    OFF_V3_URL = "https://world.openfoodfacts.org/api/v3/product/{barcode}.json"
    OFF_V2_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    OBF_V3_URL = "https://world.openbeautyfacts.org/api/v3/product/{barcode}.json"
    OBF_V2_URL = "https://world.openbeautyfacts.org/api/v2/product/{barcode}.json"
    USER_AGENT = "EcoScanAR-App/1.0 (https://github.com/ecoscan-ar; support@ecoscan.app)"

    REQUESTED_FIELDS = [
        "product_name",
        "product_name_en",
        "generic_name",
        "generic_name_en",
        "brands",
        "brand_owner",
        "categories",
        "categories_tags",
        "image_url",
        "image_front_url",
        "image_front_small_url",
        "ingredients_text",
        "ingredients_text_en",
        "ingredients",
        "packaging",
        "packaging_text",
        "packagings",
        "ecoscore_grade",
        "ecoscore_score",
        "ecoscore_data",
        "environmental_score_grade",
        "environmental_score_score",
        "environmental_score_data",
        "nutriscore_grade",
        "nutriscore_score",
        "nutriscore_data",
        "nutrition_grade_fr",
        "nova_group",
        "nutriments",
        "allergens",
        "allergens_tags",
        "additives_tags",
        "ingredients_analysis_tags",
        "quantity",
        "serving_size",
        "countries_tags",
    ]
    REQUESTED_FIELDS_STR = ",".join(REQUESTED_FIELDS)

    @classmethod
    def fetch_by_barcode(cls, barcode: str) -> Optional[Dict[str, Any]]:
        clean_code = str(barcode).strip()
        headers = {"User-Agent": cls.USER_AGENT}
        params = {"fields": cls.REQUESTED_FIELDS_STR}
        off_timeout = False
        obf_timeout = False

        # 1. Query Open Food Facts API v3
        try:
            url_v3 = cls.OFF_V3_URL.format(barcode=clean_code)
            resp = requests.get(url_v3, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if (data.get("status") == 1 or data.get("status") == "success" or data.get("result", {}).get("id") == "product_found") and "product" in data:
                    return cls._normalize_product(data["product"], clean_code, "Open Food Facts API")
        except requests.exceptions.Timeout as e:
            print(f"[OFF v3 TIMEOUT] Open Food Facts v3 timed out for {clean_code}: {e}")
            off_timeout = True
        except Exception as e:
            print(f"[OFF v3 ERROR] Failed querying Open Food Facts v3: {e}")

        # Fallback to Open Food Facts API v2
        try:
            url_v2 = cls.OFF_V2_URL.format(barcode=clean_code)
            resp = requests.get(url_v2, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == 1 and "product" in data:
                    return cls._normalize_product(data["product"], clean_code, "Open Food Facts API")
        except requests.exceptions.Timeout as e:
            print(f"[OFF v2 TIMEOUT] Open Food Facts v2 timed out for {clean_code}: {e}")
            off_timeout = True
        except Exception as e:
            print(f"[OFF v2 ERROR] Failed querying Open Food Facts v2: {e}")

        # 2. Query Open Beauty Facts for cosmetics/hygiene products
        try:
            url_obf = cls.OBF_V3_URL.format(barcode=clean_code)
            resp = requests.get(url_obf, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if (data.get("status") == 1 or data.get("status") == "success" or data.get("result", {}).get("id") == "product_found") and "product" in data:
                    return cls._normalize_product(data["product"], clean_code, "Open Beauty Facts API")
        except requests.exceptions.Timeout as e:
            print(f"[OBF TIMEOUT] Open Beauty Facts timed out for barcode {clean_code}: {e}")
            obf_timeout = True
        except Exception as e:
            print(f"[OBF ERROR] Failed querying Open Beauty Facts: {e}")

        if off_timeout and obf_timeout:
            raise ExternalAPITimeoutException(f"External product registry request timed out for barcode '{clean_code}'.")

        return None

    @classmethod
    def _normalize_product(cls, p: Dict[str, Any], barcode: str, source_name: str) -> Dict[str, Any]:
        # Extract best available name
        name = (
            p.get("product_name_en")
            or p.get("product_name")
            or p.get("generic_name_en")
            or p.get("generic_name")
            or ""
        )
        
        # Extract brand
        brand = p.get("brands") or p.get("brand_owner") or ""
        
        # Extract category
        categories = p.get("categories") or p.get("categories_tags", [])
        if isinstance(categories, list) and categories:
            category = categories[0].replace("en:", "").replace("-", " ").title()
        elif isinstance(categories, str) and categories:
            category = categories.split(",")[0].strip()
        else:
            category = ""

        # Extract image
        image_url = (
            p.get("image_url")
            or p.get("image_front_url")
            or p.get("image_front_small_url")
            or ""
        )

        # Extract complete ingredients
        ingredients_text = (
            p.get("ingredients_text_en")
            or p.get("ingredients_text")
            or ""
        )
        raw_ingredients_list = p.get("ingredients") or []
        cleaned_ingredients = cls._clean_ingredients_list(raw_ingredients_list)

        # Extract packaging (direct text, or extract from packagings array)
        packaging = p.get("packaging") or p.get("packaging_text") or ""
        packagings_list = p.get("packagings") or []
        if not packaging and isinstance(packagings_list, list) and packagings_list:
            extracted_parts = []
            for item in packagings_list:
                if isinstance(item, dict):
                    shape = item.get("shape", {})
                    if isinstance(shape, dict) and shape.get("id"):
                        extracted_parts.append(shape["id"].replace("en:", "").replace("-", " ").title())
                    elif isinstance(shape, str) and shape:
                        extracted_parts.append(shape.replace("en:", "").replace("-", " ").title())

                    material = item.get("material", {})
                    if isinstance(material, dict) and material.get("id"):
                        extracted_parts.append(material["id"].replace("en:", "").replace("-", " ").title())
                    elif isinstance(material, str) and material:
                        extracted_parts.append(material.replace("en:", "").replace("-", " ").title())
            if extracted_parts:
                packaging = ", ".join(dict.fromkeys(extracted_parts))

        # Extract Environmental Score data (support API v3 environmental_score_* & legacy ecoscore_*)
        ecoscore_data = p.get("environmental_score_data") or p.get("ecoscore_data") or {}
        ecoscore_grade = (
            p.get("environmental_score_grade")
            or p.get("ecoscore_grade")
            or p.get("eco_score_grade")
            or ecoscore_data.get("grade")
        )
        ecoscore_score = (
            p.get("environmental_score_score")
            or p.get("ecoscore_score")
            or p.get("eco_score_numeric")
            or ecoscore_data.get("score")
        )

        nutriscore_grade = p.get("nutriscore_grade") or p.get("nutrition_grade_fr")
        nutriscore_data = p.get("nutriscore_data") or {}
        nutriscore_score = p.get("nutriscore_score") or nutriscore_data.get("score")
        nova_group = p.get("nova_group")
        countries = p.get("countries_tags", [])
        nutriments = p.get("nutriments", {})
        ingredients_analysis_tags = p.get("ingredients_analysis_tags", [])
        allergens = p.get("allergens") or ""
        allergens_tags = [t.replace("en:", "").replace("-", " ").title() for t in p.get("allergens_tags", [])]
        additives_tags = [t.replace("en:", "").upper() for t in p.get("additives_tags", [])]
        quantity = p.get("quantity") or ""
        serving_size = p.get("serving_size") or ""

        return {
            "barcode": barcode,
            "product_name": str(name).strip(),
            "brand": str(brand).strip(),
            "category": str(category).strip(),
            "quantity": str(quantity).strip(),
            "serving_size": str(serving_size).strip(),
            "image_url": str(image_url).strip(),
            "ingredients_text": str(ingredients_text).strip(),
            "ingredients": cleaned_ingredients,
            "packaging": str(packaging).strip(),
            "packagings": packagings_list,
            "ecoscore_grade": str(ecoscore_grade).strip().lower() if ecoscore_grade and str(ecoscore_grade).strip().lower() in ["a", "b", "c", "d", "e"] else None,
            "ecoscore_score": int(ecoscore_score) if ecoscore_score is not None and str(ecoscore_score).isdigit() else None,
            "nutriscore_grade": str(nutriscore_grade).upper() if nutriscore_grade and str(nutriscore_grade).strip().lower() in ["a", "b", "c", "d", "e"] else None,
            "nutriscore_score": int(nutriscore_score) if nutriscore_score is not None and str(nutriscore_score).lstrip('-').isdigit() else None,
            "nova_group": int(nova_group) if nova_group is not None and str(nova_group).isdigit() else None,
            "countries": countries,
            "ecoscore_data": ecoscore_data,
            "nutriments": nutriments,
            "allergens": str(allergens).strip(),
            "allergens_tags": allergens_tags,
            "additives_tags": additives_tags,
            "ingredients_analysis_tags": ingredients_analysis_tags,
            "source": source_name
        }

    @classmethod
    def _clean_ingredients_list(cls, ingredients_raw: Any) -> List[Dict[str, Any]]:
        """Recursively parses and normalizes the ingredient tree with nested sub-ingredients."""
        if not isinstance(ingredients_raw, list):
            return []

        results = []
        for item in ingredients_raw:
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("id", "").replace("en:", "").replace("-", " ").title()
            if not text:
                continue

            sub_items = cls._clean_ingredients_list(item.get("ingredients"))
            
            percent = item.get("percent_estimate") or item.get("percent")
            try:
                percent_val = round(float(percent), 1) if percent is not None else None
            except (ValueError, TypeError):
                percent_val = None

            results.append({
                "text": text.strip(),
                "percent": percent_val,
                "vegan": item.get("vegan"),
                "vegetarian": item.get("vegetarian"),
                "from_palm_oil": item.get("from_palm_oil") == "yes",
                "sub_ingredients": sub_items
            })
        return results
