"""Data models for decoding service."""
from typing import Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class DecodingRequest(BaseModel):
    """Request model for decoding."""
    latent: Union[str, object] = Field(..., description="Path to latent .pt file, tensor object, or dict format")
    vae_model_name: Optional[str] = Field(
        default="qwen_image_vae.safetensors",
        description="Name of VAE model file"
    )
    output_filename: Optional[str] = Field(
        default="output",
        description="Base name for output image file"
    )
    output_dir: Optional[str] = Field(
        default="./output",
        description="Directory to save output image"
    )
    output_format: Optional[str] = Field(
        default="jpg",
        description="Output image format: jpg, png, or webp"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier"
    )


class DecodingResponse(BaseModel):
    """Response model for decoding."""
    status: str = Field(..., description="Status: success or error")
    request_id: str = Field(..., description="Request identifier")
    image_file_path: Optional[str] = Field(
        default=None,
        description="Path to saved image file"
    )
    image_shape: Optional[List[int]] = Field(
        default=None,
        description="Shape of decoded image (height, width, channels)"
    )
    image_tensor: Optional[object] = Field(
        default=None,
        description="Image tensor (if not saved)"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="Size of output file in bytes"
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


class KafkaDecodingRequest(BaseModel):
    """Kafka message model for decoding requests."""
    request_id: str
    correlation_id: Optional[str] = None
    latent: str  # File path
    vae_model_name: Optional[str] = "qwen_image_vae.safetensors"
    output_filename: Optional[str] = "output"
    output_dir: Optional[str] = "./output"
    output_format: Optional[str] = "jpg"
    timestamp: Optional[int] = None


class KafkaDecodingResponse(BaseModel):
    """Kafka message model for decoding responses."""
    request_id: str
    correlation_id: Optional[str] = None
    status: str
    image_file_path: Optional[str] = None
    image_shape: Optional[List[int]] = None
    file_size: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: str



