"""
GPU status endpoint for CPU Bridge scheduler.
"""
from fastapi import APIRouter, Request, Depends
from app.service.auth import require_internal_auth
from app.service.scheduler import get_scheduler
from app.service.config import get_node_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gpu", tags=["gpu"])


@router.get("/status")
async def get_gpu_status(request: Request):
    """
    Get GPU status for CPU Bridge scheduler.
    
    Returns:
        Status with busy, current_job_id, queue_length
    """
    # Require internal auth
    await require_internal_auth(request)
    
    scheduler = get_scheduler()
    status = scheduler.get_status()
    
    return {
        "node_id": get_node_id(),
        **status
    }

