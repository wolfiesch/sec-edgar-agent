from edgar import set_identity
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.data.db import init_db

from .config import settings
from .exceptions import SecApiError
from .routes import chat, filings, health, ingest, search, tables

# Configure edgartools identity immediately
set_identity(settings.SEC_USER_AGENT)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLM-ready SEC filing data with structured tables and citations",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
def on_startup():
    init_db()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(SecApiError)
async def sec_api_exception_handler(request: Request, exc: SecApiError):
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

@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": settings.VERSION
    }
