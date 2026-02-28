from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Forza Python a riconoscere i percorsi corretti per evitare ModuleNotFoundError
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.dirname(current_dir))

try:
    from webapp.services.staticanalysis.app.routers.detect_smell import router
except ModuleNotFoundError:
    try:
        from app.routers.detect_smell import router
    except ModuleNotFoundError:
        from routers.detect_smell import router

app = FastAPI(title="Static Analysis Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)