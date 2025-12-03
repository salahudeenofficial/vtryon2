"""
Tryon endpoint for virtual try-on inference.
"""
import asyncio
import json
import tempfile
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Form, Request, HTTPException, status
from typing import Optional
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.service.auth import require_internal_auth
from app.service.scheduler import get_scheduler
from app.service.config import get_node_id
from app.service.inference import run_inference
from app.service.asset_callback import send_callback, send_error_callback
from app.service.utils_image import validate_image_file, save_uploaded_file, cleanup_file
from app.service.logger import log_event
from models.request_models import TryonResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tryon"])


@router.post("/tryon", response_model=TryonResponse, status_code=status.HTTP_202_ACCEPTED)
async def tryon(
    request: Request,
    job_id: str = Form(...),
    user_id: str = Form(...),
    session_id: str = Form(...),
    provider: str = Form(...),
    masked_user_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    config: Optional[str] = Form(None),
):
    """
    Virtual try-on endpoint.
    
    Accepts job and returns 202 immediately.
    Runs inference asynchronously and sends result via callback.
    
    Returns:
        202 Accepted if job accepted
        429 Too Many Requests if GPU busy
        401 Unauthorized if auth fails
    """
    # Require internal auth
    await require_internal_auth(request)
    
    # Validate provider
    if provider != "qwen":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {provider}. Must be 'qwen'"
        )
    
    # Log request received
    log_event(
        logger,
        "request_received",
        f"Tryon request received for job {job_id}",
        job_id=job_id,
        user_id=user_id,
        session_id=session_id
    )
    
    # Check GPU availability
    scheduler = get_scheduler()
    if not scheduler.can_accept_job():
        log_event(
            logger,
            "gpu_busy_rejected",
            f"GPU busy, rejecting job {job_id}",
            job_id=job_id
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "job_id": job_id,
                "status": "REJECTED_BUSY",
                "node_id": get_node_id(),
                "message": "GPU is busy. Try another node."
            },
            headers={
                "Retry-After": "1",
                "X-Node-Id": get_node_id()
            }
        )
    
    # Accept job
    if not scheduler.accept_job(job_id):
        # This shouldn't happen if can_accept_job() returned True, but handle it
        log_event(
            logger,
            "gpu_busy_rejected",
            f"GPU busy (race condition), rejecting job {job_id}",
            job_id=job_id
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "job_id": job_id,
                "status": "REJECTED_BUSY",
                "node_id": get_node_id(),
                "message": "GPU is busy. Try another node."
            },
            headers={
                "Retry-After": "1",
                "X-Node-Id": get_node_id()
            }
        )
    
    log_event(
        logger,
        "validation_passed",
        f"Job {job_id} validated and accepted",
        job_id=job_id
    )
    
    # Parse config if provided
    inference_config = {}
    if config:
        try:
            inference_config = json.loads(config)
        except json.JSONDecodeError:
            logger.warning(f"Invalid config JSON for job {job_id}, using defaults")
    
    # Start background task
    asyncio.create_task(
        process_inference_async(
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            masked_user_image=masked_user_image,
            garment_image=garment_image,
            prompt=inference_config.get("prompt", "将图片 1 中的绿色遮罩区域仅用于判断服装属于上半身或下半身，不要将服装限制在遮罩范围内。\n\n将图片 2 中的服装自然地穿戴到图片 1 中的人物身上，保持图片 2 中服装的完整形状、袖长和轮廓。无论图片 2 是单独的服装图还是人物穿着该服装的图，都应准确地转移服装，同时保留其原始面料质感、材质细节和颜色准确性。\n\n确保图片 1 中人物的面部、头发和皮肤完全保持不变。光照与阴影应自然匹配图片 1 的环境，但服装的材质外观必须忠实于图片 2。\n\n保持边缘平滑融合、阴影逼真，整体效果自然且不改变人物的身份特征"),
            seed=inference_config.get("seed"),
            steps=inference_config.get("steps", 4),
            cfg=inference_config.get("cfg", 1.0),
        )
    )
    
    # Return 202 immediately
    return TryonResponse(
        job_id=job_id,
        status="ACCEPTED",
        node_id=get_node_id()
    )


async def process_inference_async(
    job_id: str,
    user_id: str,
    session_id: str,
    masked_user_image: UploadFile,
    garment_image: UploadFile,
    prompt: str,
    seed: Optional[int],
    steps: int,
    cfg: float,
) -> None:
    """
    Process inference asynchronously.
    
    Steps:
    1. Validate images
    2. Save temporary files
    3. Run inference
    4. Send callback
    5. Cleanup
    """
    temp_masked_path = None
    temp_garment_path = None
    output_image_path = None
    
    try:
        log_event(
            logger,
            "inference_started",
            f"Inference started for job {job_id}",
            job_id=job_id
        )
        
        # Save uploaded files temporarily
        temp_masked_path = save_uploaded_file(masked_user_image)
        temp_garment_path = save_uploaded_file(garment_image)
        
        # Validate images
        is_valid, error_msg = validate_image_file(temp_masked_path)
        if not is_valid:
            raise ValueError(f"Invalid masked_user_image: {error_msg}")
        
        is_valid, error_msg = validate_image_file(temp_garment_path)
        if not is_valid:
            raise ValueError(f"Invalid garment_image: {error_msg}")
        
        # Run inference
        output_image_path, inference_time_ms = await run_inference(
            masked_user_image_path=temp_masked_path,
            garment_image_path=temp_garment_path,
            prompt=prompt,
            seed=seed,
            steps=steps,
            cfg=cfg,
        )
        
        log_event(
            logger,
            "inference_completed",
            f"Inference completed for job {job_id} in {inference_time_ms:.0f}ms",
            job_id=job_id,
            inference_time_ms=inference_time_ms
        )
        
        # Send callback to Asset Service
        success = await send_callback(
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            output_image_path=output_image_path,
            inference_time_ms=inference_time_ms,
        )
        
        if not success:
            logger.error(f"Failed to send callback for job {job_id}")
        
    except Exception as e:
        logger.error(f"Inference failed for job {job_id}: {e}", exc_info=True)
        
        # Send error callback
        await send_error_callback(
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            error=str(e),
        )
        
    finally:
        # Cleanup temporary files
        if temp_masked_path:
            cleanup_file(temp_masked_path)
        if temp_garment_path:
            cleanup_file(temp_garment_path)
        
        # Mark job as complete
        scheduler = get_scheduler()
        scheduler.complete_job(job_id)
        
        log_event(
            logger,
            "cleanup_complete",
            f"Cleanup complete for job {job_id}",
            job_id=job_id
        )

