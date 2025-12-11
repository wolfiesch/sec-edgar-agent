from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routes import health, filings, tables
from .exceptions import SecApiError

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLM-ready SEC filing data with structured tables and citations",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

from edgar import set_identity
set_identity(settings.SEC_USER_AGENT)

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
app.include_router(health.router, tags=["health"])
app.include_router(filings.router, prefix=f"{settings.API_V1_STR}/filings", tags=["filings"])
app.include_router(tables.router, prefix=f"{settings.API_V1_STR}/tables", tags=["tables"])

@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": settings.VERSION
    }
