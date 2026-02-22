from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_ANALYSIS_SERVICE = os.getenv("AI_ANALYSIS_SERVICE", "http://localhost:8001")
STATIC_ANALYSIS_SERVICE = os.getenv("STATIC_ANALYSIS_SERVICE", "http://localhost:8002")
REPORT_SERVICE = os.getenv("REPORT_SERVICE", "http://localhost:8003")

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeSmile API Gateway"}

@app.post("/api/detect_smell_static")
async def detect_smell_static(request: dict):
    request["include_callgraph"] = True 
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{STATIC_ANALYSIS_SERVICE}/detect_smell_static", 
                json=request
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        return {"success": False, "error": str(exc)}

@app.post("/api/detect_smell_ai")
async def detect_smell_ai(request: dict):
    try:
        async with httpx.AsyncClient(timeout=500.0) as client:
            response = await client.post(
                f"{AI_ANALYSIS_SERVICE}/detect_smell_ai",
                json=request,
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        return {"success": False, "error": str(exc)}

@app.post("/api/generate_report")
async def generate_report(request: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{REPORT_SERVICE}/generate_report", json=request)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        return {"success": False, "error": str(exc)}