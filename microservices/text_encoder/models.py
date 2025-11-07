"""Data models for text encoder service."""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class TextEncoderRequest(BaseModel):
    """Request model for text encoding."""
    image1_path: str = Field(..., description="Path to first image file (masked person - needs scaling)")
    image2_path: str = Field(..., description="Path to second image file (cloth image)")
    prompt: str = Field(..., description="Text prompt for positive conditioning")
    negative_prompt: Optional[str] = Field(
        default="",
        description="Text prompt for negative conditioning"
    )
    clip_model_name: Optional[str] = Field(
        default="qwen_2.5_vl_7b_fp8_scaled.safetensors",
        description="Name of CLIP model file"
    )
    vae_model_name: Optional[str] = Field(
        default="qwen_image_vae.safetensors",
        description="Name of VAE model file"
    )
    upscale_method: Optional[str] = Field(
        default="lanczos",
        description="Image scaling method for image1"
    )
    megapixels: Optional[float] = Field(
        default=1.0,
        description="Target megapixels for scaling image1"
    )
    output_dir: Optional[str] = Field(
        default="./output",
        description="Directory to save outputs"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier"
    )


class TextEncoderResponse(BaseModel):
    """Response model for text encoding."""
    status: str = Field(..., description="Status: success or error")
    request_id: str = Field(..., description="Request identifier")
    positive_encoding_file_path: Optional[str] = Field(
        default=None,
        description="Path to saved positive encoding tensor file"
    )
    negative_encoding_file_path: Optional[str] = Field(
        default=None,
        description="Path to saved negative encoding tensor file"
    )
    positive_encoding_shape: Optional[List[int]] = Field(
        default=None,
        description="Shape of positive encoding tensor"
    )
    negative_encoding_shape: Optional[List[int]] = Field(
        default=None,
        description="Shape of negative encoding tensor"
    )
    positive_encoding_tensor: Optional[object] = Field(
        default=None,
        description="Positive encoding tensor (if not saved)"
    )
    negative_encoding_tensor: Optional[object] = Field(
        default=None,
        description="Negative encoding tensor (if not saved)"
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


class KafkaTextEncoderRequest(BaseModel):
    """Kafka message model for text encoder requests."""
    request_id: str
    correlation_id: Optional[str] = None
    image1_path: str
    image2_path: str
    prompt: str
    negative_prompt: Optional[str] = ""
    clip_model_name: Optional[str] = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
    vae_model_name: Optional[str] = "qwen_image_vae.safetensors"
    upscale_method: Optional[str] = "lanczos"
    megapixels: Optional[float] = 1.0
    output_dir: Optional[str] = "./output"
    timestamp: Optional[int] = None


class KafkaTextEncoderResponse(BaseModel):
    """Kafka message model for text encoder responses."""
    request_id: str
    correlation_id: Optional[str] = None
    status: str
    positive_encoding_file_path: Optional[str] = None
    negative_encoding_file_path: Optional[str] = None
    positive_encoding_shape: Optional[List[int]] = None
    negative_encoding_shape: Optional[List[int]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: str



