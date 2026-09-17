from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models.schemas import HealthResponse
from app.api.profile import router as profile_router
from app.api.skill_gap import router as skill_gap_router
from app.api.training import router as training_router
from app.api.geographic import router as geographic_router
from app.api.simulator import router as simulator_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI and data-driven employment & skill intelligence backend for SKILL PULSE.",
)

# Robust CORS configuration for smooth frontend communication without unsafe wildcards
# Uses all_cors_origins (local + FRONTEND_URL/CORS_EXTRA_ORIGINS env) and regex for *.vercel.app
# Localhost always allowed; production Vercel URL injected via env var without code change
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    return {
        "project": "SKILL PULSE API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }


@app.get(f"{settings.API_PREFIX}/health", response_model=HealthResponse, tags=["System Health"])
def health_check():
    """
    Health check endpoint returning system status and engine version.
    """
    return HealthResponse(status="ok", version=settings.VERSION)


# Include Feature Routers
app.include_router(profile_router, prefix=settings.API_PREFIX)
app.include_router(skill_gap_router, prefix=settings.API_PREFIX)
app.include_router(training_router, prefix=settings.API_PREFIX)
app.include_router(geographic_router, prefix=settings.API_PREFIX)
app.include_router(simulator_router, prefix=settings.API_PREFIX)



