from fastapi import APIRouter, HTTPException
from app.models.schemas import SimulatorRunRequest, SimulatorRunResponse
from app.services.simulator_service import simulator_service

router = APIRouter(prefix="/simulator", tags=["What-If Policy Simulator"])


@router.post("/run", response_model=SimulatorRunResponse)
def run_simulation(request: SimulatorRunRequest):
    """
    What-If Policy Simulator Endpoint:
    Simulates deterministic baseline vs scenario after a training capacity intervention.
    Reuses skill-gap alignment and geographic opportunity logic. All scores bounded 0-100.
    Labeled PROTOTYPE_BASELINE / rule-based per context.md — no predictive certainty.
    """
    try:
        result = simulator_service.run_simulation(request)
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while running simulation: {str(e)}"
        )
