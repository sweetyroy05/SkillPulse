from fastapi import APIRouter, HTTPException
from app.models.schemas import GeographicAnalyzeRequest, GeographicAnalyzeResponse
from app.services.geographic_service import geographic_service

router = APIRouter(prefix="/geographic", tags=["Geographic Skill Intelligence"])


@router.post("/analyze", response_model=GeographicAnalyzeResponse)
def analyze_geographic_intelligence(request: GeographicAnalyzeRequest):
    """
    Geographic Skill Intelligence Endpoint:
    Analyzes local skill demand, regional skill shortages, high-demand competencies,
    and emerging geographic employment opportunities based on prototype benchmark data.
    """
    try:
        result = geographic_service.analyze_geographic_intelligence(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing geographic skill intelligence: {str(e)}"
        )
