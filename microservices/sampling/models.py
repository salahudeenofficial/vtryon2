"""Data models for sampling service."""
from typing import Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class SamplingRequest(BaseModel):
    """Request model for sampling."""
    positive_encoding: Union[str, object] = Field(..., description="Path to positive encoding .pt file or tensor object")
    negative_encoding: Union[str, object] = Field(..., description="Path to negative encoding .pt file or tensor object")
    latent_image: Union[str, object] = Field(..., description="Path to latent image .pt file or tensor object")
    unet_model_name: Optional[str] = Field(
        default="qwen_image_edit_2509_fp8_e4m3fn.safetensors",
        description="Name of UNET model file"
    )
    lora_model_name: Optional[str] = Field(
        default="Qwen-Image-Lightning-4steps-V2.0.safetensors",
        description="Name of LoRA model file"
    )
    lora_strength: Optional[float] = Field(
        default=1.0,
        description="LoRA strength"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed (None for random)"
    )
    steps: Optional[int] = Field(
        default=4,
        description="Number of sampling steps"
    )
    cfg: Optional[float] = Field(
        default=1.0,
        description="CFG scale"
    )
    sampler_name: Optional[str] = Field(
        default="euler",
        description="Sampler name"
    )
    scheduler: Optional[str] = Field(
        default="simple",
        description="Scheduler name"
    )
    denoise: Optional[float] = Field(
        default=1.0,
        description="Denoise strength"
    )
    shift: Optional[int] = Field(
        default=3,
        description="AuraFlow shift parameter"
    )
    strength: Optional[float] = Field(
        default=1.0,
        description="CFGNorm strength parameter"
    )
    output_dir: Optional[str] = Field(
        default="./output",
        description="Directory to save outputs"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier"
    )


class SamplingResponse(BaseModel):
    """Response model for sampling."""
    status: str = Field(..., description="Status: success or error")
    request_id: str = Field(..., description="Request identifier")
    sampled_latent_file_path: Optional[str] = Field(
        default=None,
        description="Path to saved sampled latent tensor file"
    )
    sampled_latent_shape: Optional[List[int]] = Field(
        default=None,
        description="Shape of sampled latent tensor"
    )
    sampled_latent_tensor: Optional[object] = Field(
        default=None,
        description="Sampled latent tensor (if not saved)"
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


class KafkaSamplingRequest(BaseModel):
    """Kafka message model for sampling requests."""
    request_id: str
    correlation_id: Optional[str] = None
    positive_encoding: str  # File path
    negative_encoding: str  # File path
    latent_image: str  # File path
    unet_model_name: Optional[str] = "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    lora_model_name: Optional[str] = "Qwen-Image-Lightning-4steps-V2.0.safetensors"
    lora_strength: Optional[float] = 1.0
    seed: Optional[int] = None
    steps: Optional[int] = 4
    cfg: Optional[float] = 1.0
    sampler_name: Optional[str] = "euler"
    scheduler: Optional[str] = "simple"
    denoise: Optional[float] = 1.0
    shift: Optional[int] = 3
    strength: Optional[float] = 1.0
    output_dir: Optional[str] = "./output"
    timestamp: Optional[int] = None


class KafkaSamplingResponse(BaseModel):
    """Kafka message model for sampling responses."""
    request_id: str
    correlation_id: Optional[str] = None
    status: str
    sampled_latent_file_path: Optional[str] = None
    sampled_latent_shape: Optional[List[int]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: str



