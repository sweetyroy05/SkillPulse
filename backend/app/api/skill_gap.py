from fastapi import APIRouter, HTTPException
from app.models.schemas import SkillGapAnalyzeRequest, SkillGapAnalyzeResponse
from app.services.skill_gap_service import skill_gap_service

router = APIRouter(prefix="/skill-gap", tags=["Skill Gap Radar"])


@router.post("/analyze", response_model=SkillGapAnalyzeResponse)
def analyze_skill_gap(request: SkillGapAnalyzeRequest):
    """
    Skill Gap Radar Endpoint:
    Compares candidate skills against target occupational role requirements,
    computes deterministic alignment scores, and identifies prioritized missing competencies.
    """
    try:
        result = skill_gap_service.analyze_skill_gap(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing skill gap: {str(e)}"
        )
