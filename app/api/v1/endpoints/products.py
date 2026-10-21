from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.product_retrieval_service import ProductRetrievalService
from app.services.open_food_facts_service import ExternalAPITimeoutException
from app.services.gemini_service import analyze_product_sustainability

router = APIRouter()

@router.get("/product/{barcode}")
async def get_product(barcode: str):
    clean_code = str(barcode).strip()
    if not clean_code or clean_code == "0000000000000":
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "status": "not_found",
                "message": f"Product with barcode '{clean_code}' was not found in verified database or external registries."
            }
        )

    try:
        result = ProductRetrievalService.get_product(clean_code)
    except ExternalAPITimeoutException:
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "status": "timeout",
                "message": f"External product registry timed out for barcode '{clean_code}'. Please try again."
            }
        )
    except Exception as e:
        print(f"[SERVER ERROR] Error fetching product '{clean_code}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "server_error",
                "message": "Internal server error occurred while retrieving product."
            }
        )

    if result is None:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "status": "not_found",
                "message": f"Product with barcode '{clean_code}' was not found in verified database or external registries."
            }
        )

    product_data = result["product"]
    raw_sustainability = result.get("raw_sustainability", {})

    # Generate contextual insights without inventing facts
    try:
        insights = await analyze_product_sustainability(product_data, raw_sustainability)
        product_data["ai_explanation"] = insights.get("ai_explanation", "")
        product_data["eco_tip"] = insights.get("eco_tip", "")
        product_data["sustainable_alternative"] = insights.get("sustainable_alternative", "")
        product_data["sustainability_tag"] = insights.get("sustainability_tag", "Verified Product")
        product_data["what_this_means_for_you"] = insights.get("what_this_means_for_you", [])
        product_data["ai_provenance"] = insights.get("provenance", "unavailable")
    except Exception as e:
        print(f"[INSIGHTS ERROR] In product endpoint: {e}")
        product_data["ai_explanation"] = "Insights unavailable."
        product_data["eco_tip"] = ""
        product_data["sustainable_alternative"] = ""
        product_data["sustainability_tag"] = "Verified Product"
        product_data["what_this_means_for_you"] = []
        product_data["ai_provenance"] = "unavailable"

    return {
        "success": True,
        "status": "success",
        "barcode": clean_code,
        "source": result["source"],
        "product": product_data,
        "environment": result.get("environment"),
        "nutrition": result.get("nutrition"),
        "ingredients": result.get("ingredients"),
        "packaging": result.get("packaging"),
        "provenance": result.get("provenance")
    }

@router.get("/products/featured")
def get_featured_products(limit: int = 10):
    products = ProductRetrievalService.get_featured_products(limit=limit)
    return {
        "success": True,
        "status": "success",
        "count": len(products),
        "products": products
    }