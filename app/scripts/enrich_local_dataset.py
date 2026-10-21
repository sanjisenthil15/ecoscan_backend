import json
import os
import requests
import time

test_barcodes = [
    '8901058851298',
    '8901058022193',
    '8901719134845',
    '8901030699085',
    '8901725121181',
    '8901063016941',
    '8901058000269'
]

HEADERS = {'User-Agent': 'EcoScanAR-App/1.0 (https://github.com/ecoscan-ar; support@ecoscan.app)'}
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'verified_indian_products.json')

def enrich_barcodes(barcodes):
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        local_data = json.load(f)

    for b in barcodes:
        print(f"Fetching {b} from Open Food Facts v3...")
        try:
            r = requests.get(f'https://world.openfoodfacts.org/api/v3/product/{b}.json', headers=HEADERS, timeout=15)
            if r.status_code == 200:
                d = r.json()
                if (d.get('status') == 1 or d.get('status') == 'success' or d.get('result', {}).get('id') == 'product_found') and 'product' in d:
                    p = d['product']
                    rec = local_data.get(b, {'barcode': b})
                    
                    name = p.get('product_name_en') or p.get('product_name') or rec.get('product_name')
                    brand = p.get('brands') or p.get('brand_owner') or rec.get('brand')
                    cat = p.get('categories') or rec.get('category')
                    img = p.get('image_url') or p.get('image_front_url') or rec.get('image_url')
                    
                    rec['product_name'] = str(name).strip() if name else rec.get('product_name', 'Not available')
                    rec['brand'] = str(brand).strip() if brand else rec.get('brand', 'Not available')
                    rec['category'] = str(cat).strip() if cat else rec.get('category', 'Not available')
                    if img:
                        rec['image_url'] = str(img).strip()
                    
                    ing_text = p.get('ingredients_text_en') or p.get('ingredients_text') or rec.get('ingredients_text')
                    if ing_text:
                        rec['ingredients_text'] = str(ing_text).strip()
                    if p.get('ingredients'):
                        rec['ingredients'] = p.get('ingredients')
                    
                    rec['allergens'] = p.get('allergens', '')
                    rec['allergens_tags'] = p.get('allergens_tags', [])
                    rec['additives_tags'] = p.get('additives_tags', [])
                    rec['ingredients_analysis_tags'] = p.get('ingredients_analysis_tags', [])
                    
                    if p.get('nutriments'):
                        rec['nutriments'] = p.get('nutriments')
                    
                    eco_data = p.get('ecoscore_data') or p.get('environmental_score_data') or {}
                    rec['ecoscore_data'] = eco_data
                    grade = p.get('ecoscore_grade') or p.get('environmental_score_grade') or eco_data.get('grade')
                    score = p.get('ecoscore_score') or p.get('environmental_score_score') or eco_data.get('score')
                    if grade and str(grade).lower() in ['a', 'b', 'c', 'd', 'e']:
                        rec['ecoscore_grade'] = str(grade).lower()
                    if score is not None:
                        try:
                            rec['ecoscore_score'] = int(score)
                        except:
                            pass
                    
                    pack = p.get('packaging') or p.get('packaging_text')
                    if pack:
                        rec['packaging'] = str(pack).strip()
                    if p.get('packagings'):
                        rec['packagings'] = p.get('packagings')
                    
                    nutri = p.get('nutriscore_grade')
                    if nutri and str(nutri).lower() in ['a', 'b', 'c', 'd', 'e']:
                        rec['nutriscore_grade'] = str(nutri).upper()
                    nova = p.get('nova_group')
                    if nova:
                        rec['nova_group'] = int(nova)
                    
                    rec['source'] = 'Open Food Facts (Verified Indian Product)'
                    local_data[b] = rec
                    print(f"  [SUCCESS] {b}: {rec['product_name']} (EcoScore: {rec.get('ecoscore_score')}, Grade: {rec.get('ecoscore_grade')})")
            else:
                print(f"  [HTTP {r.status_code}] for {b}")
        except Exception as e:
            print(f"  [ERROR] {b}: {e}")
        time.sleep(0.5)

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(local_data, f, indent=2, ensure_ascii=False)
    print("Dataset successfully updated!")

if __name__ == '__main__':
    enrich_barcodes(test_barcodes)
