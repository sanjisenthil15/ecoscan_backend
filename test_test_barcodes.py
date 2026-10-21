from app.services.product_retrieval_service import ProductRetrievalService

barcodes = [
    '8901058851298',
    '8901058022193',
    '8901719134845',
    '8901030699085',
    '8901725121181',
    '8901063016941'
]

for b in barcodes:
    res = ProductRetrievalService.get_product(b)
    if res:
        p = res['product']
        print(f"\n=== Barcode: {b} ===")
        print(f"  Name: {p.get('product_name')} ({p.get('brand')})")
        print(f"  Eco Score: {p.get('eco_score')} | Grade: {p.get('eco_score_grade')} | Provenance: {p.get('eco_score_provenance_label')}")
        print(f"  Carbon: {p.get('carbon_footprint')} | Label: {p.get('carbon_footprint_label')}")
        print(f"  Water: {p.get('water_usage')} | Label: {p.get('water_usage_label')}")
        print(f"  Water Explanation: {p.get('water_usage_explanation')}")
        print(f"  Packaging: {p.get('packaging_recyclability')} | Label: {p.get('packaging_label')}")
    else:
        print(f"\n=== Barcode: {b} -> Not found in registry ===")
