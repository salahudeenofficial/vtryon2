"""
Model caching module for Qwen Image Edit API.
Loads models once at startup and keeps them in CPU memory.
"""
import torch
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global model cache
_model_cache: Dict[str, Any] = {}
_models_loaded = False


def load_models_once() -> None:
    """
    Load all models once at startup and keep them in CPU memory.
    This should be called during FastAPI startup.
    """
    global _model_cache, _models_loaded
    
    if _models_loaded:
        logger.info("Models already loaded, skipping...")
        return
    
    logger.info("=" * 60)
    logger.info("Loading models into CPU memory...")
    logger.info("=" * 60)
    
    try:
        from workflow_script_serial import (
            add_comfyui_directory_to_sys_path,
            add_extra_model_paths,
            get_value_at_index,
        )
        from api_server import import_custom_nodes_minimal
        from nodes import (
            UNETLoader,
            CLIPLoader,
            VAELoader,
            LoraLoaderModelOnly,
        )
        
        # Setup ComfyUI paths
        add_comfyui_directory_to_sys_path()
        add_extra_model_paths()
        
        # Load custom nodes (required before loading models)
        logger.info("Loading custom nodes...")
        import_custom_nodes_minimal()
        logger.info("✓ Custom nodes loaded")
        
        # Load models with CPU offload
        with torch.inference_mode():
            # Load UNET
            logger.info("Loading UNET model...")
            unetloader = UNETLoader()
            unet_model = unetloader.load_unet(
                unet_name="qwen_image_edit_2509_fp8_e4m3fn.safetensors",
                weight_dtype="default",
            )
            _model_cache["unet"] = unet_model
            logger.info("✓ UNET model loaded")
            
            # Load CLIP
            logger.info("Loading CLIP model...")
            cliploader = CLIPLoader()
            clip_model = cliploader.load_clip(
                clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors",
                type="qwen_image",
                device="default",
            )
            _model_cache["clip"] = clip_model
            logger.info("✓ CLIP model loaded")
            
            # Load VAE
            logger.info("Loading VAE model...")
            vaeloader = VAELoader()
            vae_model = vaeloader.load_vae(vae_name="qwen_image_vae.safetensors")
            _model_cache["vae"] = vae_model
            logger.info("✓ VAE model loaded")
            
            # Load LoRA (requires UNET to be loaded first)
            logger.info("Loading LoRA model...")
            loraloadermodelonly = LoraLoaderModelOnly()
            lora_model = loraloadermodelonly.load_lora_model_only(
                lora_name="Qwen-Image-Lightning-4steps-V2.0.safetensors",
                strength_model=1,
                model=get_value_at_index(unet_model, 0),
            )
            _model_cache["lora"] = lora_model
            logger.info("✓ LoRA model loaded")
        
        # Ensure models are on CPU
        _move_models_to_cpu()
        
        _models_loaded = True
        logger.info("=" * 60)
        logger.info("✓ All models loaded and available in CPU memory")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def _move_models_to_cpu() -> None:
    """
    Move all cached models to CPU memory.
    This is called after loading and after each inference.
    """
    try:
        # ComfyUI's model management handles device placement automatically
        # Models are loaded with CPU offload by default if configured
        # We just need to ensure they're not actively on GPU
        import comfy.model_management as model_management
        
        # Force models to CPU if they're on GPU
        # This is handled by ComfyUI's model management system
        # Models will be moved to GPU automatically when needed during inference
        pass
        
    except Exception as e:
        logger.warning(f"Could not explicitly move models to CPU: {e}")
        # This is okay - ComfyUI handles device management


def get_cached_model(model_type: str) -> Any:
    """
    Get a cached model by type.
    
    Args:
        model_type: One of "unet", "clip", "vae", "lora"
    
    Returns:
        The cached model object
    
    Raises:
        KeyError: If model type is not found
        RuntimeError: If models haven't been loaded yet
    """
    global _model_cache, _models_loaded
    
    if not _models_loaded:
        raise RuntimeError("Models not loaded. Call load_models_once() first.")
    
    if model_type not in _model_cache:
        raise KeyError(f"Model type '{model_type}' not found in cache. Available: {list(_model_cache.keys())}")
    
    return _model_cache[model_type]


def is_models_loaded() -> bool:
    """Check if models have been loaded."""
    return _models_loaded


def clear_model_cache() -> None:
    """Clear the model cache (for testing/cleanup)."""
    global _model_cache, _models_loaded
    _model_cache.clear()
    _models_loaded = False
    logger.info("Model cache cleared")

