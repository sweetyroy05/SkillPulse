from fastapi import APIRouter, HTTPException
from app.models.schemas import TrainingImpactAnalyzeRequest, TrainingImpactAnalyzeResponse
from app.services.training_service import training_service

router = APIRouter(prefix="/training-impact", tags=["Training Impact Analyzer"])


@router.post("/analyze", response_model=TrainingImpactAnalyzeResponse)
def analyze_training_impact(request: TrainingImpactAnalyzeRequest):
    """
    Training Impact Analyzer Endpoint:
    Simulates the impact of targeted training programs against candidate skill gaps,
    computes projected alignment boosts, evaluates local employment alignment,
    and returns prioritized course recommendations.
    """
    try:
        result = training_service.analyze_training_impact(request)
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while analyzing training impact: {str(e)}"
        )
