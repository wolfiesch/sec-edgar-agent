"""Health check route for uptime monitoring."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sec-api-llm",
        "version": "0.1.0"
    }
