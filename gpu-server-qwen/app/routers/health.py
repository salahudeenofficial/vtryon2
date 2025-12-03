"""
Health check endpoint.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter
from app.service.config import get_node_id
from model_cache import is_models_loaded
import torch
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """
    Health check endpoint.
    
    Returns:
        Status with gpu_available, model_loaded, node_id
    """
    gpu_available = torch.cuda.is_available() if torch.cuda else False
    model_loaded = is_models_loaded()
    
    return {
        "status": "ok",
        "gpu_available": gpu_available,
        "model_loaded": model_loaded,
        "node_id": get_node_id(),
    }

