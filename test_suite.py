from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("[PASS] /health endpoint", flush=True)

def test_maggi_product():
    # 8901058851298 - Maggi Noodles Masala
    response = client.get("/product/8901058851298")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Maggi" in p["product_name"] or "Maggi" in p["brand"]
    assert p["carbon_footprint_status"] in ["official_calculated", "category_lca"]
    assert "Product-specific water impact unavailable" in p["water_usage"] or p["water_usage_status"] == "unavailable"
    assert p["eco_score"] is not None or p["eco_score_grade"] is not None
    assert p["ingredients_text"] != "Not available"
    assert "nutriments" in p
    assert "energy_kcal" in p["nutriments"]
    print(f"[PASS] 8901058851298: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']}) | Carbon: {p['carbon_footprint']}")

def test_maggi_noodles_variant():
    # 8901058022193 - Maggi Noodles variant
    response = client.get("/product/8901058022193")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Maggi" in p["product_name"] or "Maggi" in p["brand"]
    assert p["eco_score"] == 65
    assert p["eco_score_grade"] == "b"
    print(f"[PASS] 8901058022193: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']})")

def test_parle_g():
    # 8901719134845 - Parle-G Biscuit
    response = client.get("/product/8901719134845")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Parle" in p["product_name"] or "Parle" in p["brand"]
    assert p["eco_score"] == 37
    assert p["eco_score_grade"] == "d"
    assert p["nutriscore_grade"] == "E"
    assert p["nova_group"] == 4
    print(f"[PASS] 8901719134845: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']})")

def test_kissan_ketchup():
    # 8901030699085 - Tomato Ketchup Kissan
    response = client.get("/product/8901030699085")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Ketchup" in p["product_name"] or "Kissan" in p["brand"]
    assert p["eco_score"] == 74
    assert p["eco_score_grade"] == "b"
    print(f"[PASS] 8901030699085: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']})")

def test_aashirvaad_atta():
    # 8901725121181 - Aashirvaad Whole Wheat Flour
    response = client.get("/product/8901725121181")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Wheat" in p["product_name"] or "Aashirvaad" in p["brand"]
    assert p["eco_score"] == 82
    assert p["eco_score_grade"] == "a"
    assert p["nutriscore_grade"] == "A"
    assert p["nova_group"] == 1
    print(f"[PASS] 8901725121181: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']})")

def test_britannia_classic():
    # 8901063016941 - Britannia Classic
    response = client.get("/product/8901063016941")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Britannia" in p["brand"] or "Classic" in p["product_name"]
    # Does NOT fabricate fake scores when missing
    assert p["eco_score"] is None
    print(f"[PASS] 8901063016941: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']})")

def test_maggi_special_masala():
    # 8901058000269 - Maggi Special Masala
    response = client.get("/product/8901058000269")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    p = data["product"]
    assert "Maggi" in p["product_name"] or "Maggi" in p["brand"]
    print(f"[PASS] 8901058000269: {p['product_name']} | EcoScore: {p['eco_score']} (Grade {p['eco_score_grade']})")

def test_featured_products():
    response = client.get("/products/featured?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["products"]) == 5
    print(f"[PASS] /products/featured returned {len(data['products'])} verified products")

def test_nonexistent_barcode():
    # 0000000000000
    response = client.get("/product/0000000000000")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()
    print(f"[PASS] 0000000000000: Status {response.status_code} with clean error: {data['message']}")

def test_structured_contract():
    # Verify response schema contains environment, nutrition, ingredients, packaging, provenance
    response = client.get("/product/8901058851298")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "nutrition" in data
    assert "ingredients" in data
    assert "packaging" in data
    assert "provenance" in data
    print("[PASS] Full structured JSON contract verified")

if __name__ == "__main__":
    test_health()
    test_maggi_product()
    test_maggi_noodles_variant()
    test_parle_g()
    test_kissan_ketchup()
    test_aashirvaad_atta()
    test_britannia_classic()
    test_maggi_special_masala()
    test_featured_products()
    test_nonexistent_barcode()
    test_structured_contract()
    print("\nALL BACKEND AUTOMATED TESTS PASSED!")
