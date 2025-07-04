import json

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from wallet_service.infrastructure.cache.cache_service import CacheService


class CacheMiddleware:
    """HTTP caching middleware for GET requests."""

    def __init__(self, cache: CacheService) -> None:
        self.cache = cache

    async def __call__(self, request: Request, call_next) -> Response:
        """Cache GET requests."""
        if request.method != "GET":
            return await call_next(request)

        cache_key = f"http:{request.url.path}:{request.url.query}"
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            return JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers={
                    **cached_response["headers"],
                    "X-Cache": "HIT"
                }
            )

        response = await call_next(request)

        if response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            await self.cache.set(
                cache_key,
                {
                    "content": json.loads(body),
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                },
                ttl=300
            )

            return Response(
                content=body,
                status_code=response.status_code,
                headers={
                    **response.headers,
                    "X-Cache": "MISS"
                },
                media_type="application/json"
            )

        return response
