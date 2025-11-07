"""Configuration management for decoding service."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for decoding service."""
    
    # Service mode: standalone or kafka
    mode = os.getenv("MODE", "standalone")
    
    # Kafka Configuration
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_request_topic = os.getenv("KAFKA_REQUEST_TOPIC", "decoding-requests")
    kafka_response_topic = os.getenv("KAFKA_RESPONSE_TOPIC", "decoding-responses")
    kafka_consumer_group = os.getenv("KAFKA_CONSUMER_GROUP", "decoding-group")
    kafka_schema_registry_url = os.getenv("KAFKA_SCHEMA_REGISTRY_URL", "http://localhost:8081")
    
    # Model Configuration
    model_dir = os.getenv("MODEL_DIR", "./models")
    vae_model_name = os.getenv("VAE_MODEL_NAME", "qwen_image_vae.safetensors")
    
    # Output Configuration
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    default_output_format = os.getenv("DEFAULT_OUTPUT_FORMAT", "jpg")  # jpg, png, webp
    
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
    
    # Logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "json")
    
    @classmethod
    def get_vae_model_path(cls) -> Path:
        """Get full path to VAE model."""
        return Path(cls.model_dir) / "vae" / cls.vae_model_name
    
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
        
        vae_path = cls.get_vae_model_path()
        if not vae_path.exists():
            raise ValueError(f"VAE model not found: {vae_path}")
        
        if cls.default_output_format not in ["jpg", "jpeg", "png", "webp"]:
            raise ValueError(f"Invalid output format: {cls.default_output_format}. Must be jpg, png, or webp")



