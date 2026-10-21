import requests

barcodes = [
    '8901725121723',
    '8901058000269',
    '8901058851298',
    '8901058022193',
    '8901719134845',
    '8901030699085',
    '8901725121181',
    '8901063016941',
    '0000000000000'
]

for b in barcodes:
    resp = requests.get(f"http://127.0.0.1:8000/product/{b}")
    data = resp.json()
    if resp.status_code == 200:
        p = data["product"]
        print(f"[STATUS 200] {b}: {p['product_name']} ({p['brand']}) | Score: {p['eco_score']} (Grade: {p['eco_score_grade']}) | Carbon: {p['carbon_footprint']} ({p['carbon_footprint_label']}) | Water: {p['water_usage']} ({p['water_usage_label']})")
    elif resp.status_code == 404:
        print(f"[STATUS 404] {b}: Product Not Found -> {data.get('message')}")
    elif resp.status_code == 504:
        print(f"[STATUS 504] {b}: Registry Timeout -> {data.get('message')}")
    else:
        print(f"[STATUS {resp.status_code}] {b}: {data}")

print("\nALL BARCODE STATUS CHECKS COMPLETED!")
