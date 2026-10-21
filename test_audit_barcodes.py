import requests
import json
import sys

barcodes = [
    ('8901725121723', 'Aashirvaad Superior MP Atta'),
    ('8901058000269', 'Maggi'),
    ('8901058851298', 'Maggi 2-Minute Noodles variant'),
    ('8901058022193', 'Maggi variant'),
    ('8901719134845', 'Parle-G'),
    ('8901030699085', 'Kissan Tomato Ketchup'),
    ('8901063016941', 'Britannia Classic'),
    ('8901725181222', 'Yippee noodles'),
    ('0000000000000', 'Unknown barcode')
]

for code, desc in barcodes:
    print('='*70, flush=True)
    print(f'TESTING BARCODE: {code} ({desc})', flush=True)
    try:
        r = requests.get(f'http://127.0.0.1:8000/product/{code}', timeout=12)
        print(f'HTTP Status: {r.status_code}', flush=True)
        if r.status_code == 200:
            data = r.json()
            prod = data.get('product', {})
            print(f"Product Name: {prod.get('product_name')}", flush=True)
            print(f"Brand: {prod.get('brand')}", flush=True)
            print(f"Category: {prod.get('category')}", flush=True)
            print(f"EcoScore: {prod.get('eco_score')} | Grade: {prod.get('eco_score_grade')} | Provenance: {prod.get('eco_score_provenance_label')}", flush=True)
            print(f"Carbon: {prod.get('carbon_footprint')} | Label: {prod.get('carbon_footprint_label')}", flush=True)
            print(f"Water: {prod.get('water_usage')} | Label: {prod.get('water_usage_label')}", flush=True)
            print(f"Packaging: {prod.get('packaging')} | Recyclability: {prod.get('packaging_recyclability')}", flush=True)
            print(f"Nutri-Score: {prod.get('nutriscore_grade')} | NOVA: {prod.get('nova_group')}", flush=True)
            ing = str(prod.get('ingredients_text', ''))
            print(f"Ingredients: {ing[:80] + '...' if len(ing) > 80 else ing}", flush=True)
            print(f"Source: {prod.get('source')}", flush=True)
        else:
            print(f"Response: {r.json().get('message')}", flush=True)
    except Exception as e:
        print(f"Exception: {e}", flush=True)

print("AUDIT FINISHED", flush=True)
