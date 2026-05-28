"""FastAPI main application for AgentFlow."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import chat, approvals, audit, gdpr, agents
from .middleware.tenant import TenantMiddleware

# Create FastAPI application
app = FastAPI(
    title="AgentFlow API",
    description="Multi-agent workflow orchestration platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant context middleware
app.add_middleware(TenantMiddleware)

# Include routers with /api prefix
app.include_router(chat.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(gdpr.router, prefix="/api")
app.include_router(agents.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "agentflow-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AgentFlow API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url)
        }
    )