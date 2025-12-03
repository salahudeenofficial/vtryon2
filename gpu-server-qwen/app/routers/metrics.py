"""
Metrics endpoint for Prometheus-style metrics.
"""
from fastapi import APIRouter
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])

# Simple in-memory metrics (can be replaced with Prometheus client)
_metrics: Dict[str, float] = {
    "vton_inference_count": 0,
    "vton_inference_latency_ms": 0,
    "vton_inference_errors_total": 0,
    "gpu_memory_used_bytes": 0,
    "gpu_utilization_percent": 0,
}


def increment_metric(name: str, value: float = 1.0) -> None:
    """Increment a metric."""
    if name in _metrics:
        _metrics[name] += value


def set_metric(name: str, value: float) -> None:
    """Set a metric value."""
    _metrics[name] = value


@router.get("/metrics")
async def metrics():
    """
    Metrics endpoint.
    
    Returns:
        Dictionary of metrics
    """
    # Update GPU metrics if available
    try:
        import torch
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated() if torch.cuda else 0
            set_metric("gpu_memory_used_bytes", gpu_memory)
    except Exception:
        pass
    
    return _metrics

