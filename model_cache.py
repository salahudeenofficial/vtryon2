"""
Model Cache Manager for FastAPI Server
Loads and caches ComfyUI models to keep them warm in memory across requests.
"""
import torch
from typing import Optional, Dict, Any
import logging

# Global model cache
_model_cache: Dict[str, Any] = {}
_models_loaded = False

logger = logging.getLogger(__name__)


def get_model_cache() -> Dict[str, Any]:
    """Get the global model cache dictionary."""
    return _model_cache


def is_models_loaded() -> bool:
    """Check if models have been loaded."""
    return _models_loaded


def load_models_once() -> Dict[str, Any]:
    """
    Load all required models once and cache them.
    This should be called at FastAPI startup.
    
    Returns:
        Dictionary containing all loaded models
    """
    global _model_cache, _models_loaded
    
    if _models_loaded:
        logger.info("Models already loaded, returning cached models")
        return _model_cache
    
    logger.info("Loading models for the first time...")
    
    from workflow_script_serial import import_custom_nodes_minimal, get_value_at_index
    from nodes import (
        UNETLoader,
        CLIPLoader,
        VAELoader,
        LoraLoaderModelOnly,
    )
    
    # Load custom nodes (only once)
    import_custom_nodes_minimal()
    
    with torch.inference_mode():
        # Load UNET model
        logger.info("Loading UNET model...")
        unetloader = UNETLoader()
        unet_model = unetloader.load_unet(
            unet_name="qwen_image_edit_2509_fp8_e4m3fn.safetensors",
            weight_dtype="default",
        )
        _model_cache["unet"] = get_value_at_index(unet_model, 0)
        logger.info("✓ UNET model loaded")
        
        # Load CLIP model
        logger.info("Loading CLIP model...")
        cliploader = CLIPLoader()
        clip_model = cliploader.load_clip(
            clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors",
            type="qwen_image",
            device="default",
        )
        _model_cache["clip"] = get_value_at_index(clip_model, 0)
        logger.info("✓ CLIP model loaded")
        
        # Load VAE model
        logger.info("Loading VAE model...")
        vaeloader = VAELoader()
        vae_model = vaeloader.load_vae(vae_name="qwen_image_vae.safetensors")
        _model_cache["vae"] = get_value_at_index(vae_model, 0)
        logger.info("✓ VAE model loaded")
        
        # Load LoRA model
        logger.info("Loading LoRA model...")
        loraloadermodelonly = LoraLoaderModelOnly()
        lora_model = loraloadermodelonly.load_lora_model_only(
            lora_name="Qwen-Image-Lightning-4steps-V2.0.safetensors",
            strength_model=1,
            model=_model_cache["unet"],
        )
        _model_cache["lora_model"] = get_value_at_index(lora_model, 0)
        logger.info("✓ LoRA model loaded")
        
        # Store loader instances for reuse
        _model_cache["unetloader"] = unetloader
        _model_cache["cliploader"] = cliploader
        _model_cache["vaeloader"] = vaeloader
        _model_cache["loraloadermodelonly"] = loraloadermodelonly
        
        # Ensure models are loaded into GPU memory using ComfyUI's model management
        logger.info("Loading models into GPU memory...")
        try:
            import comfy.model_management as model_management
            # Load UNET model into GPU
            model_management.load_models_gpu([_model_cache["unet"]], force_full_load=True)
            logger.info("✓ UNET model loaded into GPU")
            
            # Note: CLIP and VAE are typically loaded on-demand, but we can preload them too
            # For now, they'll be loaded when first used
        except Exception as e:
            logger.warning(f"Could not explicitly load models into GPU: {e}")
            logger.info("Models will be loaded on-demand (this is normal for CLIP/VAE)")
        
        _models_loaded = True
        logger.info("✓ All models loaded and cached successfully!")
        
        # Log memory usage
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3  # GB
            logger.info(f"GPU Memory - Allocated: {memory_allocated:.2f} GB, Reserved: {memory_reserved:.2f} GB")
    
    return _model_cache


def get_cached_model(model_type: str) -> Any:
    """
    Get a cached model by type.
    
    Args:
        model_type: One of "unet", "clip", "vae", "lora_model"
    
    Returns:
        The cached model object
    
    Raises:
        KeyError: If model type not found or models not loaded
    """
    if not _models_loaded:
        raise RuntimeError("Models not loaded. Call load_models_once() first.")
    
    if model_type not in _model_cache:
        raise KeyError(f"Model type '{model_type}' not found in cache. Available: {list(_model_cache.keys())}")
    
    return _model_cache[model_type]


# Import get_value_at_index from workflow_script_serial for use in load_models_once
# We need to import it after the function definition to avoid circular imports
# This will be imported inside load_models_once() to avoid issues

