from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import query, tools, company

app = FastAPI(
    title="SEC EDGAR Agent API",
    description="API for the Autonomous Financial Research Agent",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:5174",  # Vite dev server (alternate port)
    "http://localhost:5175",  # Vite dev server (alternate port 2)
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Note: These modules will be implemented in subsequent steps
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(company.router, prefix="/api/company", tags=["Company"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "sec-edgar-agent"}
