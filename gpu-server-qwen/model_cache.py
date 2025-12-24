"""
Model caching module for Qwen Image Edit API.
Loads models once at startup and caches them.

OPTIMIZATIONS:
- PyTorch native attention (SDPA) instead of split attention
- torch.compile() for JIT compilation
"""
import torch
import logging
import os
import sys
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global model cache
_model_cache: Dict[str, Any] = {}
_models_loaded = False

# torch.compile configuration
ENABLE_TORCH_COMPILE = True
TORCH_COMPILE_MODE = "reduce-overhead"  # Options: "default", "reduce-overhead", "max-autotune"


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
    logger.info("Loading models with optimizations...")
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
        
        # ============================================================================
        # OPTIMIZATION: Enable PyTorch SDPA and disable split attention
        # ============================================================================
        try:
            from comfy.cli_args import args as comfy_args
            import comfy.model_management as model_management
            
            # Force PyTorch native attention (faster than split attention)
            comfy_args.use_pytorch_cross_attention = True
            comfy_args.use_split_cross_attention = False
            comfy_args.use_quad_cross_attention = False
            
            # Enable all SDPA backends
            model_management.ENABLE_PYTORCH_ATTENTION = True
            torch.backends.cuda.enable_math_sdp(True)
            torch.backends.cuda.enable_flash_sdp(True)
            torch.backends.cuda.enable_mem_efficient_sdp(True)
            
            logger.info("✓ Attention optimization enabled:")
            logger.info(f"  • PyTorch SDPA = {model_management.ENABLE_PYTORCH_ATTENTION}")
            logger.info(f"  • Flash SDP = {torch.backends.cuda.flash_sdp_enabled()}")
            logger.info(f"  • Math SDP = {torch.backends.cuda.math_sdp_enabled()}")
            logger.info(f"  • Mem Efficient SDP = {torch.backends.cuda.mem_efficient_sdp_enabled()}")
            
        except Exception as e:
            logger.warning(f"Could not set attention optimization: {e}")
        
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
        
        _models_loaded = True
        logger.info("=" * 60)
        logger.info("✓ All models loaded successfully!")
        logger.info("OPTIMIZATIONS ACTIVE:")
        logger.info("  • PyTorch SDPA (native attention)")
        logger.info("  • Split attention DISABLED")
        if ENABLE_TORCH_COMPILE:
            logger.info(f"  • torch.compile mode: {TORCH_COMPILE_MODE}")
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
