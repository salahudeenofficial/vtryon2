"""Data models for latent encoder service."""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class EncodeRequest(BaseModel):
    """Request model for encoding."""
    image_path: str = Field(..., description="Path to input image file")
    vae_model_name: Optional[str] = Field(
        default="qwen_image_vae.safetensors",
        description="Name of VAE model file"
    )
    upscale_method: Optional[str] = Field(
        default="lanczos",
        description="Image scaling method"
    )
    megapixels: Optional[float] = Field(
        default=1.0,
        description="Target megapixels for scaling"
    )
    output_dir: Optional[str] = Field(
        default="./output",
        description="Directory to save outputs"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier"
    )


class EncodeResponse(BaseModel):
    """Response model for encoding."""
    status: str = Field(..., description="Status: success or error")
    request_id: str = Field(..., description="Request identifier")
    latent_file_path: Optional[str] = Field(
        default=None,
        description="Path to saved latent tensor file"
    )
    latent_shape: Optional[List[int]] = Field(
        default=None,
        description="Shape of latent tensor"
    )
    scaled_image_path: Optional[str] = Field(
        default=None,
        description="Path to scaled image if saved"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Error code if status is error"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status is error"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Timestamp of response"
    )


class KafkaMessage(BaseModel):
    """Kafka message model."""
    request_id: str
    correlation_id: Optional[str] = None
    image_path: str
    vae_model_name: Optional[str] = "qwen_image_vae.safetensors"
    output_dir: Optional[str] = "./output"
    upscale_method: Optional[str] = "lanczos"
    megapixels: Optional[float] = 1.0
    timestamp: Optional[int] = None



