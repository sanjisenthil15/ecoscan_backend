import requests
import json

barcodes = [
    '8901725121723',
    '8901058000269',
    '8901058851298',
    '8901058022193',
    '8901719134845',
    '8901030699085',
    '8901063016941',
    '8901725181222'
]

for b in barcodes:
    url = f'https://world.openfoodfacts.org/api/v3/product/{b}.json'
    r = requests.get(url, headers={'User-Agent': 'EcoScanAR-App/1.0'}, timeout=10)
    if r.status_code == 200:
        data = r.json()
        p = data.get('product', {})
        eco = p.get('ecoscore_data') or p.get('environmental_score_data') or {}
        agri = eco.get('agribalyse', {})
        packagings = p.get('packagings')
        nutriments = p.get('nutriments', {})
        print('='*70)
        print(f"BARCODE: {b} -> Name: {p.get('product_name')}")
        print(f"  Brand: {p.get('brands')}")
        print(f"  Categories: {p.get('categories')}")
        print(f"  Categories tags: {p.get('categories_tags')}")
        print(f"  Agribalyse code: {agri.get('code')} | proxy: {agri.get('proxy_code')} | is_proxy: {agri.get('is_proxy')}")
        print(f"  co2_total: {agri.get('co2_total')} | ef_total: {agri.get('ef_total')}")
        print(f"  agribalyse name_en: {agri.get('name_en')} | name_fr: {agri.get('name_fr')}")
        print(f"  agribalyse version: {agri.get('version')}")
        print(f"  agribalyse sub-metrics: co2_agriculture={agri.get('co2_agriculture')}, co2_processing={agri.get('co2_processing')}, co2_transportation={agri.get('co2_transportation')}, co2_packaging={agri.get('co2_packaging')}")
        print(f"  missing_agribalyse_match: {eco.get('missing_agribalyse_match')}")
        print(f"  ecoscore_score: {p.get('ecoscore_score')} | ecoscore_grade: {p.get('ecoscore_grade')}")
        print(f"  nutriscore_grade: {p.get('nutriscore_grade')}")
        print(f"  nutriments: energy_100g={nutriments.get('energy-kcal_100g') or nutriments.get('energy_100g')}, sugars_100g={nutriments.get('sugars_100g')}, fat_100g={nutriments.get('fat_100g')}, salt_100g={nutriments.get('salt_100g')}, proteins_100g={nutriments.get('proteins_100g')}")
        print(f"  packagings: {packagings}")
        print(f"  packaging_text: {p.get('packaging_text')}")
