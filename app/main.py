from dotenv import load_dotenv; load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.products import router as product_router

app = FastAPI(
    title="EcoScan AR Backend",
    description="Backend API for EcoScan AR",
    version="1.0.0"
)

# Enable CORS for Flutter web / Chrome
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to EcoScan AR Backend!"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)