"""Health check route — GET /api/health."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple liveness check."""
    return HealthResponse()
