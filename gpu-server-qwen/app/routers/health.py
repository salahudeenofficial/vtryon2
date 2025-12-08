"""
Health check endpoints for Load Balancer integration.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter
from app.service.config import get_node_id, get_model_type
from model_cache import is_models_loaded
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """
    Liveness probe endpoint for Load Balancer.
    
    Returns:
        Status with model_loaded, node_id
    """
    model_loaded = is_models_loaded()
    
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "node_id": get_node_id(),
    }


@router.get("/test")
async def test():
    """
    Readiness probe endpoint for Load Balancer.
    
    Returns:
        "hot" status when model_loaded is true (ready for inference)
        "loading" status when model_loaded is false (not ready)
    """
    model_loaded = is_models_loaded()
    
    if model_loaded:
        return {
            "status": "hot",
            "model_loaded": True,
            "node_id": get_node_id(),
            "model_type": get_model_type(),
        }
    else:
        return {
            "status": "loading",
            "model_loaded": False,
            "node_id": get_node_id(),
        }

