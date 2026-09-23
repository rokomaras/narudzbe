import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DEFAULT_JWT_SECRET, settings
from app.core.errors import AppError, app_error_handler, validation_error_handler
from app.core.logging import setup_logging
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.orders import router as orders_router
from app.routers.products import router as products_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging()

    if settings.ENV != "dev" and settings.JWT_SECRET == DEFAULT_JWT_SECRET:
        raise RuntimeError("Postavi JWT_SECRET env varijablu prije pokretanja u produkciji!")

    app = FastAPI(
        title="Narudzbe i dostava API",
        version="1.0.0",
        description="REST API za web-trgovinu: katalog, narudzbe, workflow dostave",
        docs_url="/docs" if settings.ENV == "dev" else None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(products_router, prefix="/products", tags=["products"])
    app.include_router(orders_router, prefix="/orders", tags=["orders"])

    logger.info("Aplikacija kreirana (env=%s)", settings.ENV)
    return app


app = create_app()
