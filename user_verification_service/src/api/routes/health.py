from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "user_verification_service"}
    )
