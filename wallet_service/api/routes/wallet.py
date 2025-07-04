from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from wallet_service.api.dependencies.utils import (
    get_cache,
    get_db_session,
    get_request_id,
    get_wallet_service,
)
from wallet_service.core.logger import Logger
from wallet_service.domain.schemas.responses import WalletResponse
from wallet_service.infrastructure.cache.cache_service import CacheService
from wallet_service.services.wallet_service import WalletService

router = APIRouter(tags=["wallet"])
logger = Logger()


@router.get(
    "/wallet/{user_id}",
    response_model=WalletResponse,
    responses={
        404: {"description": "Wallet not found"},
        400: {"description": "Invalid network"},
        500: {"description": "Internal server error"}
    }
)
async def get_wallet(
        user_id: str,
        network: str = Query(..., description="Blockchain network"),
        wallet_service: WalletService = Depends(get_wallet_service),
        request_id: str = Depends(get_request_id)
) -> WalletResponse:
    """Get wallet address for user on specified network."""
    logger.info(
        "Wallet lookup request",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "network": network
        }
    )

    if network.lower() not in ["ethereum", "tron", "bitcoin"]:
        raise HTTPException(status_code=400, detail=f"Invalid network: {network}")

    try:
        wallet = await wallet_service.get_wallet(user_id=user_id, network=network.lower())

        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return WalletResponse(
            user_id=wallet.user_id,
            network=wallet.network.value,
            wallet_address=wallet.wallet_address,
            created_at=wallet.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get wallet: {e}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "network": network
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", include_in_schema=False)
async def health_check(request: Request, db_session=Depends(get_db_session), cache: CacheService = Depends(get_cache)) -> dict:
    """Health check endpoint with dependency checks."""
    health_status = {"status": "healthy", "service": "wallet-service", "checks": {}}

    try:
        await db_session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception:
        health_status["checks"]["database"] = "failed"
        health_status["status"] = "unhealthy"

    try:
        await cache.set("health_check", "ok", ttl=10)
        health_status["checks"]["cache"] = "ok"
    except Exception:
        health_status["checks"]["cache"] = "failed"
        health_status["status"] = "unhealthy"

    if hasattr(request.app.state, "kafka_consumer"):
        health_status["checks"]["kafka_consumer"] = ("ok" if request.app.state.kafka_consumer._running else "failed")

    return health_status
