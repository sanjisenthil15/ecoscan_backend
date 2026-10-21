import json
import os
import requests

DATA_PATH = "app/data/verified_indian_products.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    products = json.load(f)

print(f"Total products in local dataset: {len(products)}")

test_barcodes = [
    "8901058851298",
    "8901058022193",
    "8901719134845",
    "8901030699085",
    "8901725121181",
    "8901063016941"
]

print("\n--- LOCAL RECORD CHECK FOR TEST BARCODES ---")
for b in test_barcodes:
    if b in products:
        p = products[b]
        print(f"Barcode: {b}")
        print(f"  Name: {p.get('product_name')}")
        print(f"  Brand: {p.get('brand')}")
        print(f"  Category: {p.get('category')}")
        print(f"  Packaging: {p.get('packaging')}")
        print(f"  Eco Grade: {p.get('ecoscore_grade')}")
        print(f"  Eco Score: {p.get('ecoscore_score')}")
        print(f"  Ingredients: {p.get('ingredients_text')[:60] if p.get('ingredients_text') else 'None'}...")
    else:
        print(f"Barcode: {b} -> NOT in local verified json")

print("\n--- QUERYING OPEN FOOD FACTS LIVE FOR TEST BARCODES ---")
headers = {"User-Agent": "EcoScanAR-Audit/1.0"}
for b in test_barcodes:
    url = f"https://world.openfoodfacts.org/api/v2/product/{b}.json"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == 1:
                prod = d.get("product", {})
                eco_data = prod.get("ecoscore_data", {})
                agri = eco_data.get("agribalyse", {})
                print(f"\n[OFF LIVE] Barcode: {b}")
                print(f"  Product Name: {prod.get('product_name')}")
                print(f"  Brands: {prod.get('brands')}")
                print(f"  Categories: {prod.get('categories')}")
                print(f"  Packaging: {prod.get('packaging')} / tags: {prod.get('packaging_tags')}")
                print(f"  Ecoscore Grade: {prod.get('ecoscore_grade')}")
                print(f"  Ecoscore Score: {prod.get('ecoscore_score')}")
                print(f"  Eco Data Grade/Score: {eco_data.get('grade')} / {eco_data.get('score')}")
                print(f"  Agribalyse: {agri}")
                print(f"  Eco Data Adjustments: {eco_data.get('adjustments')}")
                print(f"  Nutriscore: {prod.get('nutriscore_grade')}")
            else:
                print(f"\n[OFF LIVE] Barcode: {b} -> Status {d.get('status')} (Not found)")
        else:
            print(f"\n[OFF LIVE] Barcode: {b} -> HTTP {r.status_code}")
    except Exception as e:
        print(f"\n[OFF LIVE] Barcode: {b} -> Error: {e}")
