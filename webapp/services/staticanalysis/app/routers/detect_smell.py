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
async def detect_smell_static(payload: DetectSmellRequest):
    analysis_result = detect_static(payload.code_snippet)
    return DetectSmellStaticResponse(
        success=analysis_result["success"],
        smells=analysis_result["response"],
    )