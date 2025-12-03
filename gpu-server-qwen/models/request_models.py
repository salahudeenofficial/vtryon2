"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class TryonRequest(BaseModel):
    """Request model for /tryon endpoint (for documentation)."""
    job_id: str = Field(..., description="Unique job identifier")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    provider: str = Field(default="qwen", description="Provider (always 'qwen')")
    config: Optional[str] = Field(None, description="JSON string with inference settings")


class TryonResponse(BaseModel):
    """Response model for /tryon endpoint."""
    job_id: str
    status: str
    node_id: str


class GPUStatusResponse(BaseModel):
    """Response model for /gpu/status endpoint."""
    node_id: str
    busy: bool
    current_job_id: Optional[str]
    queue_length: int


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    gpu_available: bool
    model_loaded: bool
    node_id: str


class VersionResponse(BaseModel):
    """Response model for /version endpoint."""
    model_type: str
    model_version: str
    backend: str
    git_commit: str
    node_id: str

