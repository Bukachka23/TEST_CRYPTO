import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from user_verification_service.src.core.logger import Logger

logger = Logger()


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        logger.info(f"Request started: {request.method} {request.url.path}", extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        })

        response = await call_next(request)
        duration = time.perf_counter() - start_time

        logger.info(f"Request completed: {request.method} {request.url.path}", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": duration
        })

        response.headers["X-Process-Time"] = str(duration)
        return response
