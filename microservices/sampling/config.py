"""Configuration management for sampling service."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for sampling service."""
    
    # Service mode: standalone or kafka
    mode = os.getenv("MODE", "standalone")
    
    # Kafka Configuration
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_request_topic = os.getenv("KAFKA_REQUEST_TOPIC", "sampling-requests")
    kafka_response_topic = os.getenv("KAFKA_RESPONSE_TOPIC", "sampling-responses")
    kafka_consumer_group = os.getenv("KAFKA_CONSUMER_GROUP", "sampling-group")
    kafka_schema_registry_url = os.getenv("KAFKA_SCHEMA_REGISTRY_URL", "http://localhost:8081")
    
    # Model Configuration
    model_dir = os.getenv("MODEL_DIR", "./models")
    unet_model_name = os.getenv("UNET_MODEL_NAME", "qwen_image_edit_2509_fp8_e4m3fn.safetensors")
    lora_model_name = os.getenv("LORA_MODEL_NAME", "Qwen-Image-Lightning-4steps-V2.0.safetensors")
    lora_strength = float(os.getenv("LORA_STRENGTH", "1.0"))
    
    # Output Configuration
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    
    # ComfyUI Configuration
    comfyui_path = os.getenv("COMFYUI_PATH", None)
    if comfyui_path is None:
        # Try to find ComfyUI in parent directories
        current_dir = Path(__file__).parent.resolve()
        comfyui_path = current_dir / "comfyui"
        if not comfyui_path.exists():
            # Look for ComfyUI in parent directories
            parent = current_dir.parent.parent
            for potential_path in [parent / "ComfyUI", parent / "comfyui"]:
                if potential_path.exists():
                    comfyui_path = potential_path
                    break
    
    # Sampling Parameters
    default_seed = os.getenv("DEFAULT_SEED", None)  # None means random
    default_steps = int(os.getenv("DEFAULT_STEPS", "4"))
    default_cfg = float(os.getenv("DEFAULT_CFG", "1.0"))
    default_sampler_name = os.getenv("DEFAULT_SAMPLER_NAME", "euler")
    default_scheduler = os.getenv("DEFAULT_SCHEDULER", "simple")
    default_denoise = float(os.getenv("DEFAULT_DENOISE", "1.0"))
    
    # Model Transformation Parameters
    default_shift = int(os.getenv("DEFAULT_SHIFT", "3"))  # AuraFlow shift
    default_strength = float(os.getenv("DEFAULT_STRENGTH", "1.0"))  # CFGNorm strength
    
    # Logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "json")
    
    @classmethod
    def get_unet_model_path(cls) -> Path:
        """Get full path to UNET model."""
        return Path(cls.model_dir) / "diffusion_models" / cls.unet_model_name
    
    @classmethod
    def get_lora_model_path(cls) -> Path:
        """Get full path to LoRA model."""
        return Path(cls.model_dir) / "loras" / cls.lora_model_name
    
    @classmethod
    def get_output_dir(cls) -> Path:
        """Get output directory path."""
        output_path = Path(cls.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        if cls.mode not in ["standalone", "kafka"]:
            raise ValueError(f"Invalid mode: {cls.mode}. Must be 'standalone' or 'kafka'")
        
        if not Path(cls.model_dir).exists():
            raise ValueError(f"Model directory does not exist: {cls.model_dir}")
        
        unet_path = cls.get_unet_model_path()
        if not unet_path.exists():
            raise ValueError(f"UNET model not found: {unet_path}")
        
        lora_path = cls.get_lora_model_path()
        if not lora_path.exists():
            raise ValueError(f"LoRA model not found: {lora_path}")



