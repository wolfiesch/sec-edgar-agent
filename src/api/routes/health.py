from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "sec-api-llm",
        "version": "0.1.0"
    }
