from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from user_verification_service.src.api.middleware.error_handler import (
    ErrorHandlerMiddleware,
)
from user_verification_service.src.api.middleware.request_logger import (
    RequestLoggerMiddleware,
)
from user_verification_service.src.api.routes.health import router as health_router
from user_verification_service.src.api.routes.verification import (
    router as verification_router,
)
from user_verification_service.src.core.config import Settings
from user_verification_service.src.core.logger import Logger
from user_verification_service.src.infrastructure.database.connection import (
    DatabaseConnection,
)
from user_verification_service.src.infrastructure.database.startup import (
    create_database_tables,
    perform_startup_checks,
)
from user_verification_service.src.infrastructure.kafka.producer import (
    KafkaEventPublisher,
)

settings = Settings()
logger = Logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting User Verification Service")
    await create_database_tables()

    kafka_publisher = KafkaEventPublisher(settings, logger)
    await kafka_publisher.get_producer()

    db_connection = DatabaseConnection(settings)

    await perform_startup_checks()

    app.state.kafka_publisher = kafka_publisher
    app.state.db_connection = db_connection

    yield

    logger.info("Shutting down User Verification Service")

    await app.state.kafka_publisher.xclose()
    await app.state.db_connection.engine.dispose()


def create_application() -> FastAPI:
    """Application factory with all configurations."""
    app = FastAPI(
        title="User Verification Service",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.include_router(verification_router)
    app.include_router(health_router)

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        workers=1,
        loop="uvloop",
        access_log=False,
        http="h11",
        timeout_keep_alive=5
    )
