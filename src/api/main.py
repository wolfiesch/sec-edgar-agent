from contextlib import asynccontextmanager
from typing import Any

from edgar import set_identity  # type: ignore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.data.db import init_db

from .config import configure_logging, settings
from .exceptions import SecApiError
from .middleware import RateLimitMiddleware, RequestLoggingMiddleware
from .routes import chat, compare, filings, health, ingest, search, tables

# Configure edgartools identity immediately
set_identity(settings.SEC_USER_AGENT)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Initialize application state."""
    configure_logging()
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLM-ready SEC filing data with structured tables and citations",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,  # Prevent 307 redirects that lose POST body
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    requests_per_hour=settings.RATE_LIMIT_REQUESTS_PER_HOUR,
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Exception Handler
@app.exception_handler(SecApiError)
async def sec_api_exception_handler(request: Request, exc: SecApiError) -> JSONResponse:
    """Translate SecApiError into an HTTP response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(filings.router, prefix=f"{settings.API_V1_STR}/filings", tags=["Filings"])
app.include_router(tables.router, prefix=f"{settings.API_V1_STR}/tables", tags=["Tables"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Search"])
app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["Ingestion"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(compare.router, prefix=f"{settings.API_V1_STR}/compare", tags=["Compare"])

@app.get("/")
async def root() -> dict[str, str]:
    """Simple root endpoint advertising docs and version."""
    return {
        "message": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": settings.VERSION
    }
