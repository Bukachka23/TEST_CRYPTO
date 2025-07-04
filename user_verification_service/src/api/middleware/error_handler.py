import contextvars
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from user_verification_service.src.core.logger import Logger

logger = Logger()

# Context variable for request ID
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {e!s}", extra={"request_id": request_id}, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id}
            )
