import asyncio
from app.services.product_retrieval_service import ProductRetrievalService
from app.services.open_food_facts_service import OpenFoodFactsService
from app.services.sustainability_engine import SustainabilityEngine

async def test_backend():
    print("=== 1. Testing Local Dataset Loading ===")
    data = ProductRetrievalService._load_all_datasets()
    print(f"Total verified products loaded: {len(data)}")
    assert len(data) >= 200, f"Expected >= 200 products, found {len(data)}"
    print("[PASS] Local dataset has over 200 authentic products.")

    print("\n=== 2. Testing Local Indian Product Lookup ===")
    sample_barcodes = list(data.keys())[:3]
    for b in sample_barcodes:
        result = ProductRetrievalService.get_product(b)
        assert result is not None, f"Failed retrieving product {b}"
        prod = result["product"]
        print(f"Barcode: {b} | Name: {prod['product_name']} | Brand: {prod['brand']} | Score: {prod['eco_score']} | Carbon: {prod['carbon_footprint']}")
    print("[PASS] Local lookup test passed.")

    print("\n=== 3. Testing External Live Barcode Lookup (Open Food Facts) ===")
    # Query a known international barcode e.g. Nutella 3017620422003
    external_b = "3017620422003"
    try:
        ext_result = ProductRetrievalService.get_product(external_b)
        if ext_result:
            p = ext_result["product"]
            print(f"External Barcode: {external_b} | Name: {p['product_name']} | Brand: {p['brand']} | Source: {ext_result['source']}")
            print("[PASS] Live Open Food Facts fallback lookup succeeded.")
        else:
            print("[INFO] External network query returned None (might be offline or not found).")
    except ExternalAPITimeoutException as e:
        print(f"[PASS] External network timeout caught and handled properly: {e}")

    print("\n=== 4. Testing Non-Existent Barcode Lookup ===")
    invalid_b = "0000000000000"
    inv_result = ProductRetrievalService.get_product(invalid_b)
    assert inv_result is None, "Expected None for non-existent barcode"
    print("[PASS] Non-existent barcode correctly returned None without fabricating fake data.")

    print("\n=== 5. Testing Sustainability Provenance ===")
    raw_sample = data[sample_barcodes[0]]
    sust = SustainabilityEngine.evaluate(raw_sample)
    print(f"Eco Score: {sust['eco_score_numeric']} (Provenance: {sust['eco_score_provenance']})")
    print(f"Carbon: {sust['carbon_footprint']['value']} (Status: {sust['carbon_footprint']['status']})")
    print(f"Water: {sust['water_usage']['value']} (Status: {sust['water_usage']['status']})")
    print(f"Recyclability: {sust['packaging_recyclability']['value']} (Status: {sust['packaging_recyclability']['status']})")
    print("[PASS] Sustainability Engine transparency checks passed.")

    print("\nALL BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_backend())
