import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TARGET_BARCODES = [
    "8901058851298",
    "8901058022193",
    "8901719134845",
    "8901030699085",
    "8901725121181",
    "8901063016941",
    "8901058000269",
    "8901719112683",
]

def verify_all():
    print("=" * 80)
    print("TASK 4 — BACKEND COMPREHENSIVE VERIFICATION")
    print("=" * 80)

    # 1. Verify /health
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"/health failed: {health_resp.status_code}"
    assert health_resp.json() == {"status": "ok"}
    print("\n[OK] GET /health -> Status 200: {'status': 'ok'}")

    # 2. Verify known products
    for barcode in TARGET_BARCODES:
        print(f"\n--- Testing Barcode: {barcode} ---")
        resp = client.get(f"/product/{barcode}")
        assert resp.status_code == 200, f"Expected 200 for {barcode}, got {resp.status_code}"
        body = resp.json()
        assert body["success"] is True, f"success != True for {barcode}"

        product = body["product"]
        env = body["environment"]
        nutri = body["nutrition"]
        ingr = body["ingredients"]
        pack = body["packaging"]
        prov = body["provenance"]

        # Exact barcode
        assert product["barcode"] == barcode, f"Barcode mismatch: {product['barcode']} vs {barcode}"
        
        # Product name & Brand
        name = product.get("product_name") or product.get("name")
        brand = product.get("brand")
        assert name and name != "Unknown Product", f"Missing name for {barcode}"
        assert brand, f"Missing brand for {barcode}"

        # Eco/Environmental grade & score
        grade = product.get("eco_score_grade")
        score = product.get("eco_score")
        score_prov = product.get("eco_score_provenance")
        if score is not None:
            assert score_prov == "official_calculated", f"Score provided but not official_calculated: {score_prov}"
            assert isinstance(score, (int, float)), f"Invalid score type: {type(score)}"
        
        # Carbon
        carbon = product.get("carbon_footprint")
        carbon_status = product.get("carbon_footprint_status")
        assert carbon, f"Carbon field missing for {barcode}"
        assert carbon_status in ["official_calculated", "category_lca", "unavailable"], f"Invalid carbon status: {carbon_status}"

        # Water status (strictly truthful, no fake baselines)
        water = product.get("water_usage")
        water_status = product.get("water_usage_status")
        assert "Product-specific water impact unavailable" in water or water_status == "unavailable", f"Fake water detected: {water}"

        # Packaging
        packaging_text = product.get("packaging")
        recyclability = product.get("packaging_recyclability")
        assert packaging_text, f"Missing packaging text for {barcode}"

        # Ingredients & Sub-ingredients
        ingr_text = product.get("ingredients_text")
        ingr_items = product.get("ingredients", [])
        assert ingr_text, f"Missing ingredients text for {barcode}"
        assert isinstance(ingr_items, list), f"Ingredients must be a list for {barcode}"

        # Nutrition
        nutriments = product.get("nutriments", {})
        assert isinstance(nutriments, dict), f"Nutriments must be a dict for {barcode}"

        # Nutri-Score & NOVA
        nutriscore = product.get("nutriscore_grade")
        nova = product.get("nova_group")

        # Provenance
        assert product.get("source"), f"Missing primary source for {barcode}"

        # Structured sections contract verification
        assert env is not None, f"Environment section missing for {barcode}"
        assert nutri is not None, f"Nutrition section missing for {barcode}"
        assert ingr is not None, f"Ingredients section missing for {barcode}"
        assert pack is not None, f"Packaging section missing for {barcode}"
        assert prov is not None, f"Provenance section missing for {barcode}"

        print(f"  * Barcode: {barcode}")
        print(f"  * Name: {name}")
        print(f"  * Brand: {brand}")
        print(f"  * Eco-Score: {score}/100 (Grade {grade}) [Prov: {score_prov}]")
        print(f"  * Carbon: {carbon} [{carbon_status}]")
        print(f"  * Water: {water} [{water_status}]")
        print(f"  * Packaging: {packaging_text} -> Recyclability: {recyclability}")
        print(f"  * Ingredients: {len(ingr_items)} structured items | Text: {ingr_text[:60]}...")
        print(f"  * Nutrition: {len(nutriments)} nutrient keys | Nutri-Score: {nutriscore} | NOVA: {nova}")
        print(f"  * Provenance: {product.get('source')}")

    # 3. Verify nonexistent barcode 0000000000000
    print("\n--- Testing Nonexistent Barcode: 0000000000000 ---")
    resp_404 = client.get("/product/0000000000000")
    assert resp_404.status_code == 404, f"Expected 404 for 0000000000000, got {resp_404.status_code}"
    body_404 = resp_404.json()
    assert body_404["success"] is False
    assert "not found" in body_404["message"].lower()
    print(f"[OK] 0000000000000 correctly returned HTTP 404: {body_404['message']}")

    print("\n" + "=" * 80)
    print("ALL 8 TARGET PRODUCTS AND ERROR SCENARIOS COMPREHENSIVELY VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    verify_all()
