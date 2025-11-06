"""Core service logic for latent encoder."""
import os
import sys
import torch
from pathlib import Path
from datetime import datetime
import time
import importlib.util

from config import Config
from errors import (
    ImageNotFoundError,
    VAEModelNotFoundError,
    EncodingFailedError,
    OutputDirNotWritableError,
    ScalingFailedError,
    ComfyUIInitializationError
)
# Import from local utils module (use importlib to avoid conflicts with ComfyUI utils)

# Get the directory of this file
_service_dir = Path(__file__).parent
_utils_path = _service_dir / "utils.py"

# Load utils module from local file
_utils_spec = importlib.util.spec_from_file_location("latent_encoder_utils", _utils_path)
_latent_encoder_utils = importlib.util.module_from_spec(_utils_spec)
_utils_spec.loader.exec_module(_latent_encoder_utils)

# Import functions from local utils
get_value_at_index = _latent_encoder_utils.get_value_at_index
add_comfyui_directory_to_sys_path = _latent_encoder_utils.add_comfyui_directory_to_sys_path
add_extra_model_paths = _latent_encoder_utils.add_extra_model_paths
generate_request_id = _latent_encoder_utils.generate_request_id
ensure_directory_exists = _latent_encoder_utils.ensure_directory_exists


def import_custom_nodes_minimal() -> None:
    """
    Minimal custom node loading using asyncio.run() without server infrastructure.
    This is lighter than the full server setup but still requires async execution.
    """
    import asyncio
    from nodes import init_extra_nodes
    
    # Simply run the async function with asyncio.run() - no server needed
    # This creates a new event loop, runs the coroutine, and closes the loop
    asyncio.run(init_extra_nodes(init_custom_nodes=True, init_api_nodes=False))


def setup_comfyui() -> None:
    """Setup ComfyUI paths and initialize."""
    comfyui_path = Path(__file__).parent / "comfyui"
    microservice_dir = Path(__file__).parent
    
    if not comfyui_path.exists():
        raise ComfyUIInitializationError(f"ComfyUI directory not found: {comfyui_path}")
    
    # Add ComfyUI to sys.path
    add_comfyui_directory_to_sys_path(comfyui_path)
    
    # Add extra model paths
    add_extra_model_paths(comfyui_path)
    
    # Configure folder_paths to use microservice's models directory
    # This must be done after ComfyUI is added to sys.path
    import folder_paths
    
    # Get microservice models directory (absolute path)
    microservice_models_dir = (microservice_dir / Config.model_dir).resolve()
    
    # Add microservice models directory to folder_paths
    # This adds it as an additional search path (not replacing the default)
    if microservice_models_dir.exists():
        # Add VAE path
        vae_path = microservice_models_dir / "vae"
        if vae_path.exists():
            folder_paths.add_model_folder_path("vae", str(vae_path), is_default=True)
            print(f"Added VAE model path: {vae_path}")
        
        # Add other model paths if they exist
        for model_type in ["checkpoints", "loras", "clip", "text_encoders", "diffusion_models"]:
            model_path = microservice_models_dir / model_type
            if model_path.exists():
                folder_paths.add_model_folder_path(model_type, str(model_path), is_default=False)
    
    # Import custom nodes
    import_custom_nodes_minimal()
    
    print("ComfyUI initialized successfully")


def encode_image_to_latent(
    image_path: str,
    vae_model_name: str = None,
    output_dir: str = None,
    upscale_method: str = "lanczos",
    megapixels: float = 1.0,
    request_id: str = None,
    save_tensor: bool = True
) -> dict:
    """
    Encode image to latent space representation.
    
    Args:
        image_path: Path to input image file
        vae_model_name: Name of VAE model file (default: from config)
        output_dir: Directory to save outputs (default: from config)
        upscale_method: Image scaling method (default: "lanczos")
        megapixels: Target megapixels for scaling (default: 1.0)
        request_id: Request identifier (auto-generated if not provided)
        save_tensor: Whether to save tensor to file (default: True)
    
    Returns:
        dict: {
            "status": "success" | "error",
            "request_id": str,
            "latent_file_path": str | None,
            "latent_shape": list | None,
            "error_message": str | None,
            "metadata": dict
        }
    """
    start_time = time.time()
    
    if request_id is None:
        request_id = generate_request_id()
    
    if vae_model_name is None:
        vae_model_name = Config.vae_model_name
    
    if output_dir is None:
        output_dir = Config.output_dir
    
    try:
        # Validate inputs - resolve to absolute path
        image_path_obj = Path(image_path)
        
        # If relative path, try to resolve it relative to current working directory first
        if not image_path_obj.is_absolute():
            # Try current directory
            if not image_path_obj.exists():
                # Try relative to microservice directory
                microservice_dir = Path(__file__).parent
                alt_path = microservice_dir / image_path
                if alt_path.exists():
                    image_path_obj = alt_path
                # Try relative to parent ComfyUI directory
                elif (microservice_dir.parent.parent / image_path).exists():
                    image_path_obj = microservice_dir.parent.parent / image_path
                # Try input directory
                elif (microservice_dir.parent.parent / "input" / image_path_obj.name).exists():
                    image_path_obj = microservice_dir.parent.parent / "input" / image_path_obj.name
        
        # Resolve to absolute path
        image_path_obj = image_path_obj.resolve()
        
        if not image_path_obj.exists():
            raise ImageNotFoundError(f"Image file not found: {image_path} (resolved to: {image_path_obj})")
        
        if not image_path_obj.is_file():
            raise ImageNotFoundError(f"Path is not a file: {image_path_obj}")
        
        # Setup ComfyUI
        setup_comfyui()
        
        # Import ComfyUI nodes
        from nodes import VAELoader, LoadImage, VAEEncode
        from nodes import NODE_CLASS_MAPPINGS
        
        # Load VAE model
        vae_model_path = Config.get_vae_model_path()
        if not vae_model_path.exists():
            raise VAEModelNotFoundError(f"VAE model not found: {vae_model_path}")
        
        vaeloader = VAELoader()
        vae_output = vaeloader.load_vae(vae_name=vae_model_name)
        vae = get_value_at_index(vae_output, 0)
        
        # Load image
        loadimage = LoadImage()
        image_output = loadimage.load_image(image=str(image_path_obj))
        image = get_value_at_index(image_output, 0)
        
        # Get original image shape
        original_shape = list(image.shape) if hasattr(image, 'shape') else None
        
        # Scale image
        if "ImageScaleToTotalPixels" not in NODE_CLASS_MAPPINGS:
            raise ScalingFailedError("ImageScaleToTotalPixels node not found in custom nodes")
        
        imagescaletototalpixels = NODE_CLASS_MAPPINGS["ImageScaleToTotalPixels"]()
        scaled_image_output = imagescaletototalpixels.EXECUTE_NORMALIZED(
            upscale_method=upscale_method,
            megapixels=megapixels,
            image=image,
        )
        scaled_image = get_value_at_index(scaled_image_output, 0)
        
        # Encode to latent
        vaeencode = VAEEncode()
        encoded_output = vaeencode.encode(
            pixels=scaled_image,
            vae=vae,
        )
        latent_raw = get_value_at_index(encoded_output, 0)
        
        # Extract tensor from latent output (might be dict with "samples" key)
        latent = latent_raw
        if isinstance(latent, dict):
            if "samples" in latent:
                latent = latent["samples"]
            elif "latent" in latent:
                latent = latent["latent"]
            elif len(latent) == 1:
                latent = list(latent.values())[0]
        
        if isinstance(latent, (list, tuple)):
            latent = latent[0]
        
        # Ensure it's a tensor
        if not isinstance(latent, torch.Tensor):
            raise EncodingFailedError(f"Expected tensor, got {type(latent)}: {latent}")
        
        # Get latent shape
        latent_shape = list(latent.shape) if hasattr(latent, 'shape') else None
        
        # Save latent tensor
        latent_file_path = None
        if save_tensor:
            output_dir_obj = ensure_directory_exists(Path(output_dir))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            latent_filename = f"latent_{request_id}_{timestamp}.pt"
            latent_file_path = output_dir_obj / latent_filename
            
            # Save tensor
            torch.save(latent, latent_file_path)
            latent_file_path = str(latent_file_path)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        metadata = {
            "original_image_shape": original_shape,
            "scaled_image_shape": list(scaled_image.shape) if hasattr(scaled_image, 'shape') else None,
            "latent_shape": latent_shape,
            "vae_model_name": vae_model_name,
            "upscale_method": upscale_method,
            "megapixels": megapixels,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        result = {
            "status": "success",
            "request_id": request_id,
            "latent_file_path": latent_file_path,
            "latent_shape": latent_shape,
            "metadata": metadata
        }
        
        # Always include tensor in result (for testing/comparison)
        # When save_tensor=False, we return the tensor directly
        # When save_tensor=True, we still include it for comparison purposes
        result["latent_tensor"] = latent
        
        return result
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        error_code = type(e).__name__
        error_message = str(e)
        
        return {
            "status": "error",
            "request_id": request_id,
            "latent_file_path": None,
            "latent_shape": None,
            "error_code": error_code,
            "error_message": error_message,
            "metadata": {
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

