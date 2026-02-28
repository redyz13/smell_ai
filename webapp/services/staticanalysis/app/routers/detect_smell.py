from fastapi import APIRouter

# Import robusti: locale (webapp...) + docker (app...)
try:
    from webapp.services.staticanalysis.app.schemas.requests import DetectSmellRequest
    from webapp.services.staticanalysis.app.schemas.responses import DetectSmellStaticResponse
    from webapp.services.staticanalysis.app.utils.static_analysis import detect_static
except ModuleNotFoundError:
    from app.schemas.requests import DetectSmellRequest
    from app.schemas.responses import DetectSmellStaticResponse
    from app.utils.static_analysis import detect_static

router = APIRouter()

@router.post("/detect_smell_static", response_model=DetectSmellStaticResponse)
def detect_smell_static(payload: DetectSmellRequest):
    files_list = []
    
    # Raccogliamo i file dal frontend
    if payload.files:
        files_list = [{"filename": f.filename, "content": f.content} for f in payload.files]
    elif payload.code_snippet:
        files_list = [{"filename": "snippet.py", "content": payload.code_snippet}]
        
    # Passiamo la lista all'analisi
    analysis_result = detect_static(files_list)
    
    # Restituiamo TUTTI i dati, incluso il graph_data!
    return DetectSmellStaticResponse(
        success=analysis_result.get("success", False),
        smells=analysis_result.get("response", []),
        graph_data=analysis_result.get("graph_data")
    )