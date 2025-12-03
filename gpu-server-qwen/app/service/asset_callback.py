"""
Asset Service callback handler.
Sends inference results to Asset Service via HTTP POST.
"""
import httpx
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from app.service.config import (
    get_asset_callback_url,
    get_asset_auth_token,
    get_asset_timeout,
    get_asset_retries,
    get_node_id,
    get_model_version,
)
from app.service.logger import log_event

logger = logging.getLogger(__name__)


async def send_callback(
    job_id: str,
    user_id: str,
    session_id: str,
    output_image_path: str,
    inference_time_ms: float,
    error: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send callback to Asset Service with inference results.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        session_id: Session identifier
        output_image_path: Path to output image file
        inference_time_ms: Inference time in milliseconds
        error: Optional error message
        meta: Optional metadata
        
    Returns:
        True if callback successful, False otherwise
    """
    callback_url = get_asset_callback_url()
    auth_token = get_asset_auth_token()
    timeout = get_asset_timeout()
    max_retries = get_asset_retries()
    
    # Prepare multipart form data
    files = {}
    data = {
        "job_id": job_id,
        "user_id": user_id,
        "session_id": session_id,
        "provider": "qwen",
        "node_id": get_node_id(),
        "model_version": get_model_version(),
        "inference_time_ms": str(int(inference_time_ms)),
    }
    
    if error:
        data["error"] = error
    
    if meta:
        import json
        data["meta"] = json.dumps(meta)
    
    # Add output image file
    file_handle = None
    if output_image_path and Path(output_image_path).exists():
        file_handle = open(output_image_path, "rb")
        files["output_image"] = (
            Path(output_image_path).name,
            file_handle,
            "image/png"
        )
    
    headers = {
        "X-Internal-Auth": auth_token,
    }
    
    # Retry logic
    last_error = None
    try:
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        callback_url,
                        data=data,
                        files=files,
                        headers=headers,
                    )
                    
                    if response.status_code == 200:
                        log_event(
                            logger,
                            "callback_sent_asset",
                            f"Callback sent successfully for job {job_id}",
                            job_id=job_id,
                            attempt=attempt + 1
                        )
                        return True
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        log_event(
                            logger,
                            "callback_retrying",
                            f"Callback failed (attempt {attempt + 1}/{max_retries}): {last_error}",
                            job_id=job_id,
                            attempt=attempt + 1
                        )
                        
            except Exception as e:
                last_error = str(e)
                log_event(
                    logger,
                    "callback_retrying",
                    f"Callback exception (attempt {attempt + 1}/{max_retries}): {last_error}",
                    job_id=job_id,
                    attempt=attempt + 1
                )
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)
    finally:
        # Close file handle if opened
        if file_handle:
            file_handle.close()
    
    # All retries failed
    log_event(
        logger,
        "callback_failed",
        f"Callback failed after {max_retries} attempts: {last_error}",
        job_id=job_id
    )
    
    return False


async def send_error_callback(
    job_id: str,
    user_id: str,
    session_id: str,
    error: str,
) -> bool:
    """
    Send error callback to Asset Service.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        session_id: Session identifier
        error: Error message
        
    Returns:
        True if callback successful, False otherwise
    """
    return await send_callback(
        job_id=job_id,
        user_id=user_id,
        session_id=session_id,
        output_image_path="",
        inference_time_ms=0,
        error=error,
    )

