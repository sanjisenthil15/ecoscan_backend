import requests
import json
import os
import time

def fetch_verified_indian_products(target_count=220):
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "verified_indian_products.json")

    headers = {
        "User-Agent": "EcoScanAR-DataCurator/1.0 (https://github.com/ecoscan-ar; support@ecoscan.app)"
    }

    products_by_barcode = {}
    print(f"Starting extraction of verified real Indian supermarket products from Open Food Facts...")

    # Strategy 1: Search by Country: India
    page = 1
    max_pages = 5
    while len(products_by_barcode) < target_count and page <= max_pages:
        url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=countries&tag_contains_0=contains&tag_0=india&json=true&page_size=100&page={page}"
        try:
            print(f"Fetching country page {page}...")
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("products", [])
                if not items:
                    break
                for item in items:
                    code = str(item.get("code") or item.get("_id") or "").strip()
                    name = item.get("product_name_en") or item.get("product_name")
                    brand = item.get("brands") or item.get("brand_owner")

                    if code and len(code) >= 8 and name and brand and code not in products_by_barcode:
                        categories = item.get("categories") or item.get("categories_tags", [])
                        if isinstance(categories, list) and categories:
                            cat_name = categories[0].replace("en:", "").replace("-", " ").title()
                        elif isinstance(categories, str) and categories:
                            cat_name = categories.split(",")[0].strip()
                        else:
                            cat_name = "Packaged Goods"

                        products_by_barcode[code] = {
                            "barcode": code,
                            "product_name": name.strip(),
                            "brand": brand.strip(),
                            "category": cat_name,
                            "ingredients_text": (item.get("ingredients_text_en") or item.get("ingredients_text") or "").strip(),
                            "packaging": (item.get("packaging") or item.get("packaging_text") or "").strip(),
                            "image_url": item.get("image_url") or item.get("image_front_url") or item.get("image_front_small_url") or "",
                            "ecoscore_grade": item.get("ecoscore_grade") if item.get("ecoscore_grade") in ["a", "b", "c", "d", "e"] else None,
                            "nutriscore_grade": item.get("nutriscore_grade", "").upper() if item.get("nutriscore_grade") else None,
                            "nova_group": item.get("nova_group"),
                            "countries": ["India"],
                            "source": "Open Food Facts (Verified Indian Product)"
                        }
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    # Strategy 2: Specific Indian Major Brands if count is still below target
    indian_brands = [
        "Amul", "Britannia", "Parle", "Tata", "Dabur", "Haldiram's", "Nestle India",
        "Marico", "Fortune", "MDH", "Everest", "ITC", "MTR", "Saffola", "Bikaji",
        "Catch", "Mother Dairy", "Priya", "Vadilal", "Balaji Wafers", "Kurkure", "Lay's India",
        "Sunfeast", "Aashirvaad", "Bingo", "Kissan", "Bournvita", "Horlicks", "Bru", "Taj Mahal Tea"
    ]

    for brand_name in indian_brands:
        if len(products_by_barcode) >= target_count:
            break
        url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={brand_name}&tagtype_0=countries&tag_contains_0=contains&tag_0=india&json=true&page_size=50"
        try:
            print(f"Searching for brand '{brand_name}'... (Current total: {len(products_by_barcode)})")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("products", [])
                for item in items:
                    code = str(item.get("code") or item.get("_id") or "").strip()
                    name = item.get("product_name_en") or item.get("product_name")
                    b = item.get("brands") or brand_name

                    if code and len(code) >= 8 and name and code not in products_by_barcode:
                        categories = item.get("categories") or item.get("categories_tags", [])
                        if isinstance(categories, list) and categories:
                            cat_name = categories[0].replace("en:", "").replace("-", " ").title()
                        elif isinstance(categories, str) and categories:
                            cat_name = categories.split(",")[0].strip()
                        else:
                            cat_name = "Packaged Goods"

                        products_by_barcode[code] = {
                            "barcode": code,
                            "product_name": name.strip(),
                            "brand": b.strip(),
                            "category": cat_name,
                            "ingredients_text": (item.get("ingredients_text_en") or item.get("ingredients_text") or "").strip(),
                            "packaging": (item.get("packaging") or item.get("packaging_text") or "").strip(),
                            "image_url": item.get("image_url") or item.get("image_front_url") or item.get("image_front_small_url") or "",
                            "ecoscore_grade": item.get("ecoscore_grade") if item.get("ecoscore_grade") in ["a", "b", "c", "d", "e"] else None,
                            "nutriscore_grade": item.get("nutriscore_grade", "").upper() if item.get("nutriscore_grade") else None,
                            "nova_group": item.get("nova_group"),
                            "countries": ["India"],
                            "source": "Open Food Facts (Verified Indian Product)"
                        }
            time.sleep(0.3)
        except Exception as e:
            print(f"Error fetching brand {brand_name}: {e}")

    # Write out verified products JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products_by_barcode, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Successfully saved {len(products_by_barcode)} verified authentic Indian products to {output_file}")
    return len(products_by_barcode)

if __name__ == "__main__":
    fetch_verified_indian_products(220)
