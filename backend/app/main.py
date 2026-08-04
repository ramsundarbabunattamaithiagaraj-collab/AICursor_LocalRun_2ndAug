"""RetailIQ Platform - FastAPI application entrypoint."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routers import (
    agents_router,
    auth_router,
    categories_router,
    customers_router,
    feedback_router,
    inventory_router,
    orders_router,
    products_router,
    rag_router,
)
from app.core.config import get_settings
from app.core.logging_config import configure_logging, get_logger
from app.db.init_db import init_db
from app.utils.exceptions import RetailIQError
from app.utils.response_wrapper import success_response

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s (%s)", settings.app.name, settings.app.version, settings.app.environment)
    init_db()
    yield
    logger.info("Shutting down %s", settings.app.name)


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description=(
        "Enterprise retail platform: product catalog, inventory, orders, "
        "customers/loyalty, JWT auth, a document RAG assistant, and a "
        "CrewAI-powered multi-agent SDLC toolkit."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.2fms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.exception_handler(RetailIQError)
async def retailiq_error_handler(request: Request, exc: RetailIQError) -> JSONResponse:
    logger.warning("Unhandled domain error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "message": str(exc), "data": None},
    )


app.include_router(auth_router.router)
app.include_router(categories_router.router)
app.include_router(products_router.router)
app.include_router(inventory_router.router)
app.include_router(customers_router.router)
app.include_router(orders_router.router)
app.include_router(rag_router.router)
app.include_router(agents_router.router)
app.include_router(feedback_router.router)


@app.get("/", tags=["Health"])
def root() -> dict:
    return success_response(
        data={"app": settings.app.name, "version": settings.app.version, "domain": settings.domain.name},
        message="RetailIQ Platform is running.",
    )


@app.get("/health", tags=["Health"])
def health() -> dict:
    return success_response(data={"status": "healthy"}, message="OK")
