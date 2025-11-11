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
        from nodes import (
            UNETLoader,
            CLIPLoader,
            VAELoader,
            LoraLoaderModelOnly,
        )
        import asyncio
        from nodes import init_extra_nodes
        
        # Setup ComfyUI paths
        add_comfyui_directory_to_sys_path()
        add_extra_model_paths()
        
        # Load custom nodes (required before loading models)
        logger.info("Loading custom nodes...")
        try:
            # Try to run in a separate thread to avoid event loop conflicts
            import threading
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(init_extra_nodes(init_custom_nodes=True, init_api_nodes=False))
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            asyncio.run(init_extra_nodes(init_custom_nodes=True, init_api_nodes=False))
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
            # Store FULL return value (not extracted) to preserve ComfyUI metadata
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
            # Store FULL return value (not extracted) to preserve ComfyUI metadata
            _model_cache["clip"] = clip_model
            logger.info("✓ CLIP model loaded")
            
            # Load VAE
            logger.info("Loading VAE model...")
            vaeloader = VAELoader()
            vae_model = vaeloader.load_vae(vae_name="qwen_image_vae.safetensors")
            # Store FULL return value (not extracted) to preserve ComfyUI metadata
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
            # Store FULL return value (not extracted) to preserve ComfyUI metadata
            _model_cache["lora"] = lora_model
            logger.info("✓ LoRA model loaded")
        
        _models_loaded = True
        logger.info("=" * 60)
        logger.info("✓ All models loaded and available in CPU memory")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def get_cached_model(model_type: str) -> Any:
    """
    Get a cached model by type.
    
    Args:
        model_type: One of "unet", "clip", "vae", "lora"
    
    Returns:
        The cached model object (full loader return value)
    
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


# Import get_value_at_index from workflow_script_serial for use in load_models_once
# We need to import it after the function definition to avoid circular imports
# This will be imported inside load_models_once() to avoid issues

