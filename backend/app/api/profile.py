from fastapi import APIRouter, HTTPException
from app.models.schemas import ProfileAnalyzeRequest, ProfileAnalyzeResponse
from app.services.profile_service import profile_service

router = APIRouter(prefix="/profile", tags=["Profile & Career Analyzer"])


@router.post("/analyze", response_model=ProfileAnalyzeResponse)
def analyze_profile(request: ProfileAnalyzeRequest):
    """
    Analyze user profile, normalize reported skills, categorize competencies,
    and identify aligned target occupational roles based on benchmark data.
    """
    try:
        result = profile_service.analyze_profile(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing the profile: {str(e)}"
        )
