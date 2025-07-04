from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from user_verification_service.src.api.dependencies.database import get_verification_service
from user_verification_service.src.api.middleware.error_handler import request_id_var
from user_verification_service.src.core.exceptions import BaseServiceException
from user_verification_service.src.core.logger import Logger
from user_verification_service.src.domain.schemas.requests import VerificationRequest, VerificationResponse
from user_verification_service.src.services.verification_service import VerificationService

router = APIRouter(tags=["verification"])
logger = Logger()


@router.post("/verify", response_model=VerificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def verify_user(
    request: VerificationRequest,
    background_tasks: BackgroundTasks,
    service: VerificationService = Depends(get_verification_service),
) -> VerificationResponse:
    logger.info("Verification request received", extra={
        "request_id": request_id_var.get(),
        "user_id": request.user_id,
        "network": request.network
    })

    try:
        verification = await service.verify_user(
            user_id=request.user_id,
            network=request.network,
            document_base64=request.document
        )

        return VerificationResponse(
            message="Verification in progress",
            verification_id=str(verification.id),
            status=verification.status.value
        )

    except BaseServiceException as e:
        logger.warning(f"Verification failed: {e.detail}", extra={"request_id": request_id_var.get()})
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e!s}", extra={"request_id": request_id_var.get()}, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
