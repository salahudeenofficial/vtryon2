"""
Version endpoint.
"""
import subprocess
from fastapi import APIRouter
from app.service.config import get_node_id, get_model_type, get_model_version
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["version"])


def get_git_commit() -> str:
    """Get git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()[:7]  # Short commit hash
    except Exception:
        pass
    return "unknown"


@router.get("/version")
async def version():
    """
    Version endpoint.
    
    Returns:
        Model version, backend, git commit, node_id
    """
    return {
        "model_type": get_model_type(),
        "model_version": get_model_version(),
        "backend": "comfyui-python",
        "git_commit": get_git_commit(),
        "node_id": get_node_id(),
    }

