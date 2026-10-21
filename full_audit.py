import json
import requests
from app.services.sustainability_engine import SustainabilityEngine

DATA_PATH = "app/data/verified_indian_products.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    products = json.load(f)

print(f"Total products in local dataset: {len(products)}")

# Check 8901063016941 in OFF
b = "8901063016941"
url = f"https://world.openfoodfacts.org/api/v2/product/{b}.json"
r = requests.get(url, headers={"User-Agent": "EcoScanAR-Audit/1.0"}, timeout=10)
if r.status_code == 200 and r.json().get("status") == 1:
    prod = r.json()["product"]
    print(f"\nBarcode {b} in OFF:")
    print(f"  Name: {prod.get('product_name')}")
    print(f"  Brand: {prod.get('brands')}")
    print(f"  Category: {prod.get('categories')}")
    print(f"  Eco Grade: {prod.get('ecoscore_grade')}")
    print(f"  Eco Score: {prod.get('ecoscore_score')}")
    print(f"  Packaging: {prod.get('packaging')}")
    print(f"  Agribalyse: {prod.get('ecoscore_data', {}).get('agribalyse')}")
else:
    print(f"\nBarcode {b} not found in OFF (status: {r.status_code})")

# Let's run a full audit across all 254 products
total = len(products)
direct_eco = 0
calculated_eco = 0
category_eco = 0
no_eco = 0

direct_carbon = 0
category_carbon = 0
no_carbon = 0

direct_water = 0
category_water = 0
no_water = 0

valid_packaging = 0
no_packaging = 0

water_val_counts = {}
carbon_val_counts = {}
eco_score_counts = {}

for barcode, p in products.items():
    # Evaluate via SustainabilityEngine
    s = SustainabilityEngine.evaluate(p)
    
    # Eco score
    eco_num = s.get("eco_score_numeric")
    eco_g = s.get("eco_score_grade")
    eco_prov = s.get("eco_score_provenance")
    
    if eco_num is not None or eco_g is not None:
        if p.get("ecoscore_score") is not None:
            direct_eco += 1
        elif p.get("ecoscore_grade") is not None:
            # Note: local json has grade but maybe not score, or converted from grade
            calculated_eco += 1
        else:
            category_eco += 1
        eco_score_counts[f"{eco_g}_{eco_num}"] = eco_score_counts.get(f"{eco_g}_{eco_num}", 0) + 1
    else:
        no_eco += 1
        
    # Carbon
    carb = s.get("carbon_footprint", {})
    c_val = carb.get("value")
    c_stat = carb.get("status")
    if c_stat == "direct_source":
        direct_carbon += 1
    elif c_stat == "methodology_calculated":
        category_carbon += 1
    else:
        no_carbon += 1
    carbon_val_counts[c_val] = carbon_val_counts.get(c_val, 0) + 1

    # Water
    wat = s.get("water_usage", {})
    w_val = wat.get("value")
    w_stat = wat.get("status")
    if w_stat == "direct_source":
        direct_water += 1
    elif w_stat == "methodology_calculated":
        category_water += 1
    else:
        no_water += 1
    water_val_counts[w_val] = water_val_counts.get(w_val, 0) + 1

    # Packaging
    pack = s.get("packaging_recyclability", {})
    if pack.get("status") != "unavailable" and pack.get("value") != "Not available":
        valid_packaging += 1
    else:
        no_packaging += 1

print("\n================== FULL DATA QUALITY AUDIT REPORT ==================")
print(f"Total products in verified dataset: {total}")
print(f"\n--- ECO SCORE ---")
print(f"Products with direct Eco Score (official numeric from OFF/db): {direct_eco}")
print(f"Products with grade from OFF (mapped to score): {calculated_eco}")
print(f"Products without Eco Score: {no_eco}")
print(f"Eco score distribution: {eco_score_counts}")

print(f"\n--- CARBON FOOTPRINT ---")
print(f"Products with direct LCA carbon: {direct_carbon}")
print(f"Products with category carbon baseline: {category_carbon}")
print(f"Products without carbon (Unavailable): {no_carbon}")
print(f"Carbon values frequency: {carbon_val_counts}")

print(f"\n--- WATER FOOTPRINT ---")
print(f"Products with direct product water footprint: {direct_water}")
print(f"Products with category water baseline: {category_water}")
print(f"Products without water (Unavailable): {no_water}")
print(f"Water values frequency: {water_val_counts}")

print(f"\n--- PACKAGING ---")
print(f"Products with valid packaging: {valid_packaging}")
print(f"Products with unavailable packaging: {no_packaging}")
