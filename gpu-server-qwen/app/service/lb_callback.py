"""
Load Balancer callback handler.
Sends job completion notifications to Load Balancer.
"""
import httpx
import logging
from typing import Optional, Dict, Any
from app.service.config import (
    get_lb_url,
    get_lb_auth_token,
    get_node_id,
)
from app.service.logger import log_event

logger = logging.getLogger(__name__)


async def send_job_complete(
    job_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send job completion callback to Load Balancer.
    
    Args:
        job_id: Job identifier (optional)
        metadata: Optional metadata dictionary
        
    Returns:
        True if callback successful, False otherwise
    """
    lb_url = get_lb_url()
    if not lb_url:
        # LB URL not configured, skip callback
        return True
    
    auth_token = get_lb_auth_token()
    node_id = get_node_id()
    
    # Prepare request body
    body = {
        "node_id": node_id,
        "metadata": metadata or {},
    }
    
    if job_id:
        body["job_id"] = job_id
    
    headers = {}
    if auth_token:
        headers["X-Internal-Auth"] = auth_token
    
    # Send callback (non-blocking, don't wait too long)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{lb_url}/job_complete",
                json=body,
                headers=headers,
            )
            
            if response.status_code == 200:
                log_event(
                    logger,
                    "lb_job_complete_sent",
                    f"Job complete callback sent to LB for job {job_id}",
                    job_id=job_id
                )
                return True
            else:
                logger.warning(
                    f"LB job_complete callback failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
    except Exception as e:
        # Don't fail on callback errors - just log
        logger.warning(f"LB job_complete callback error: {e}")
        return False


async def send_heartbeat(
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send heartbeat to Load Balancer (optional).
    
    Args:
        metadata: Optional metadata with busy state, etc.
        
    Returns:
        True if callback successful, False otherwise
    """
    lb_url = get_lb_url()
    if not lb_url:
        # LB URL not configured, skip callback
        return True
    
    auth_token = get_lb_auth_token()
    node_id = get_node_id()
    
    # Prepare request body
    body = {
        "node_id": node_id,
        "metadata": metadata or {},
    }
    
    headers = {}
    if auth_token:
        headers["X-Internal-Auth"] = auth_token
    
    # Send heartbeat (non-blocking)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{lb_url}/heartbeat",
                json=body,
                headers=headers,
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.debug(f"LB heartbeat failed: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        # Don't fail on heartbeat errors - just log
        logger.debug(f"LB heartbeat error: {e}")
        return False

