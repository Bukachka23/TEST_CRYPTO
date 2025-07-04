from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from wallet_service.api.routes import wallet_router
from wallet_service.api.routes.cache import CacheMiddleware
from wallet_service.core.config import Settings
from wallet_service.core.exceptions import MnemonicSecurityException
from wallet_service.core.logger import Logger
from wallet_service.core.middleware.error_handler import ErrorHandlerMiddleware
from wallet_service.core.middleware.request_logger import RequestLoggerMiddleware
from wallet_service.infrastructure.cache.cache_service import CacheService
from wallet_service.infrastructure.crypto.wallet_factory import WalletGeneratorFactory
from wallet_service.infrastructure.database.connection import DatabaseConnection
from wallet_service.infrastructure.database.startup import (
    create_database_tables,
    perform_startup_checks,
)
from wallet_service.infrastructure.kafka.consumer import KafkaEventConsumer
from wallet_service.infrastructure.kafka.producer import KafkaEventPublisher
from wallet_service.infrastructure.repositories.wallet_repository import (
    WalletRepository,
)
from wallet_service.services.derivation_service import DerivationService
from wallet_service.services.event_handler import EventHandler
from wallet_service.services.wallet_service import WalletService

logger = Logger()


class AppState(TypedDict):
    db_connection: DatabaseConnection
    redis_cache: CacheService
    wallet_service: WalletService
    kafka_consumer: KafkaEventConsumer
    settings: Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    logger.info("Starting Wallet Service")

    settings = Settings()

    if not settings.mnemonic:
        raise MnemonicSecurityException("MNEMONIC environment variable not set")

    db_connection = DatabaseConnection(settings)

    await create_database_tables()
    await perform_startup_checks()

    cache = CacheService(settings)

    wallet_generator_factory = WalletGeneratorFactory()

    session = db_connection.async_session()
    wallet_repository = WalletRepository(session)

    derivation_service = DerivationService(wallet_repository, cache)

    kafka_publisher = KafkaEventPublisher(settings, logger)

    wallet_service = WalletService(
        repository=wallet_repository,
        generator_factory=wallet_generator_factory,
        event_publisher=kafka_publisher,
        derivation_service=derivation_service,
        cache=cache,
        settings=settings,
        logger=logger
    )

    event_handler = EventHandler(
        wallet_service=wallet_service,
        settings=settings,
        logger=logger
    )

    # Initialize Kafka consumer
    kafka_consumer = KafkaEventConsumer(
        settings=settings,
        event_handler=event_handler,
        logger=logger
    )

    # Start consumer
    await kafka_consumer.start()

    # Set application state
    app.state.db_connection = db_connection
    app.state.redis_cache = cache
    app.state.wallet_service = wallet_service
    app.state.kafka_consumer = kafka_consumer
    app.state.settings = settings

    yield

    logger.info("Shutting down Wallet Service")

    await app.state.kafka_consumer.stop()

    await kafka_publisher.close()
    await app.state.redis_cache.close()
    await app.state.db_connection.engine.dispose()

    import gc
    gc.collect()


def create_application() -> FastAPI:
    """
    Application factory
    """
    app = FastAPI(
        title="Wallet Service",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggerMiddleware)

    @app.middleware("http")
    async def cache_middleware(request: Request, call_next):
        if hasattr(request.state, "redis_cache"):
            middleware = CacheMiddleware(request.state.redis_cache)
            return await middleware(request, call_next)
        return await call_next(request)

    app.include_router(wallet_router)

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        workers=1,
        loop="uvloop",
        access_log=False,
        timeout_keep_alive=5,
        limit_concurrency=1000,
        limit_max_requests=10000
    )
