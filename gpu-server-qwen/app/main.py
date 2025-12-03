"""
Main FastAPI application for Qwen GPU Server.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import services
from app.service.config import load_config, get_node_id
from app.service.logger import setup_logging, log_event
from app.service.auth import require_internal_auth
from model_cache import load_models_once, is_models_loaded

# Import routers
from app.routers import tryon, gpu_status, health, version, metrics

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Loads config and models at startup.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Qwen GPU Server Starting...")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        load_config()
        log_event(logger, "config_loaded", f"Configuration loaded. Node ID: {get_node_id()}")
        
        # Load models
        logger.info("Loading models into memory...")
        load_models_once()
        
        if not is_models_loaded():
            raise RuntimeError("Models failed to load")
        
        log_event(logger, "models_loaded", "All models loaded successfully")
        logger.info("=" * 60)
        logger.info("✓ Server ready to accept requests!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Qwen GPU Server",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable docs in production
    redoc_url=None,  # Disable redoc in production
)

# Add CORS middleware (if needed for internal services)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to reject traffic until models are loaded
@app.middleware("http")
async def check_models_loaded(request: Request, call_next):
    """Reject traffic until models are loaded."""
    # Allow health check even if models not loaded
    if request.url.path == "/health":
        return await call_next(request)
    
    if not is_models_loaded():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "message": "Models are still loading. Please wait.",
                "node_id": get_node_id()
            }
        )
    
    return await call_next(request)


# Register routers
app.include_router(tryon.router)
app.include_router(gpu_status.router)
app.include_router(health.router)
app.include_router(version.router)
app.include_router(metrics.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "node_id": get_node_id()
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_config=None,  # Use our JSON logging
    )

