from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from webapp.services.report.app.routers.report import router as report_router
except ModuleNotFoundError:
    from app.routers.report import router as report_router

app = FastAPI(title="Report Service")

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the router
app.include_router(report_router, tags=["Report"])