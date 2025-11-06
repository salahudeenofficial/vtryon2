"""Core service logic for sampling."""
import os
import sys
import torch
import random
from pathlib import Path
from datetime import datetime
from typing import Union
import time
import importlib.util

from config import Config
from errors import (
    UNETModelNotFoundError,
    LoRAModelNotFoundError,
    InputTensorNotFoundError,
    SamplingFailedError,
    OutputDirNotWritableError,
    ComfyUIInitializationError,
    InvalidTensorFormatError
)
# Import from local utils module (use importlib to avoid conflicts with ComfyUI utils)

# Get the directory of this file
_service_dir = Path(__file__).parent
_utils_path = _service_dir / "utils.py"

# Load utils module from local file
_utils_spec = importlib.util.spec_from_file_location("sampling_utils", _utils_path)
_sampling_utils = importlib.util.module_from_spec(_utils_spec)
_utils_spec.loader.exec_module(_sampling_utils)

# Import functions from local utils
get_value_at_index = _sampling_utils.get_value_at_index
add_comfyui_directory_to_sys_path = _sampling_utils.add_comfyui_directory_to_sys_path
add_extra_model_paths = _sampling_utils.add_extra_model_paths
generate_request_id = _sampling_utils.generate_request_id
ensure_directory_exists = _sampling_utils.ensure_directory_exists
load_tensor_from_file = _sampling_utils.load_tensor_from_file


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
        # Add diffusion_models path (for UNET)
        diffusion_models_path = microservice_models_dir / "diffusion_models"
        if diffusion_models_path.exists():
            folder_paths.add_model_folder_path("diffusion_models", str(diffusion_models_path), is_default=True)
            print(f"Added diffusion_models path: {diffusion_models_path}")
        
        # Add loras path
        loras_path = microservice_models_dir / "loras"
        if loras_path.exists():
            folder_paths.add_model_folder_path("loras", str(loras_path), is_default=True)
            print(f"Added loras path: {loras_path}")
        
        # Add other model paths if they exist
        for model_type in ["checkpoints", "clip", "vae", "text_encoders"]:
            model_path = microservice_models_dir / model_type
            if model_path.exists():
                folder_paths.add_model_folder_path(model_type, str(model_path), is_default=False)
    
    # Import custom nodes
    import_custom_nodes_minimal()
    
    print("ComfyUI initialized successfully")


def load_input_tensor(input_value: Union[str, torch.Tensor], description: str) -> torch.Tensor:
    """
    Load tensor from file path or return tensor directly.
    
    Args:
        input_value: File path (str) or tensor object
        description: Description for error messages
    
    Returns:
        torch.Tensor: Loaded tensor
    """
    if isinstance(input_value, str):
        # Load from file
        return load_tensor_from_file(input_value)
    elif isinstance(input_value, torch.Tensor):
        # Use directly
        return input_value
    else:
        raise InvalidTensorFormatError(f"{description} must be a file path (str) or torch.Tensor, got {type(input_value)}")


def prepare_conditioning(conditioning_value: Union[str, torch.Tensor, list, tuple]) -> list:
    """
    Prepare conditioning input for sampler.
    Sampler expects format: [[tensor, metadata_dict]] (list of conditioning items)
    
    Args:
        conditioning_value: File path, tensor, or already formatted conditioning
    
    Returns:
        Conditioning in format expected by sampler: [[tensor, metadata_dict]]
    """
    # If already in list/tuple format, check if it's already the right format
    if isinstance(conditioning_value, (list, tuple)):
        # Check if it's already a list of conditioning items [[tensor, dict]]
        if len(conditioning_value) > 0:
            first_item = conditioning_value[0]
            # If first item is a list/tuple, it's already in the right format
            if isinstance(first_item, (list, tuple)):
                return list(conditioning_value)  # Already correct format
            # If first item is a tensor, wrap the whole thing
            elif isinstance(first_item, torch.Tensor):
                # It's [tensor, ...] format, wrap it
                return [list(conditioning_value)]
        # Empty list, return as-is
        return list(conditioning_value)
    
    # Load tensor if needed
    tensor = load_input_tensor(conditioning_value, "Conditioning")
    
    # Return in format [[tensor, {}]] for sampler (list of conditioning items)
    return [[tensor, {}]]


def prepare_latent_image(latent_value: Union[str, torch.Tensor, dict]) -> dict:
    """
    Prepare latent image input for sampler.
    Sampler expects format: {"samples": tensor}
    
    Args:
        latent_value: File path, tensor, or dict with "samples" key
    
    Returns:
        Dict with "samples" key containing tensor
    """
    # If already in dict format with "samples" key, return as-is
    if isinstance(latent_value, dict):
        if "samples" in latent_value:
            return latent_value
        # If dict but no "samples" key, try to extract tensor
        if len(latent_value) == 1:
            tensor = list(latent_value.values())[0]
            if isinstance(tensor, torch.Tensor):
                return {"samples": tensor}
    
    # Load tensor if needed
    tensor = load_input_tensor(latent_value, "Latent image")
    
    # Wrap in dict format
    return {"samples": tensor}


def sample_latent(
    positive_encoding: Union[str, torch.Tensor, list, tuple],
    negative_encoding: Union[str, torch.Tensor, list, tuple],
    latent_image: Union[str, torch.Tensor, dict],
    unet_model_name: str = None,
    lora_model_name: str = None,
    lora_strength: float = 1.0,
    seed: int = None,
    steps: int = 4,
    cfg: float = 1.0,
    sampler_name: str = "euler",
    scheduler: str = "simple",
    denoise: float = 1.0,
    shift: int = 3,
    strength: float = 1.0,
    output_dir: str = None,
    request_id: str = None,
    save_tensor: bool = True
) -> dict:
    """
    Perform diffusion sampling using text encodings and latent image.
    
    Args:
        positive_encoding: Path to positive encoding .pt file, tensor, or conditioning format
        negative_encoding: Path to negative encoding .pt file, tensor, or conditioning format
        latent_image: Path to latent image .pt file, tensor, or dict format
        unet_model_name: Name of UNET model file (default: from config)
        lora_model_name: Name of LoRA model file (default: from config)
        lora_strength: LoRA strength (default: 1.0)
        seed: Random seed (None for random)
        steps: Number of sampling steps (default: 4)
        cfg: CFG scale (default: 1.0)
        sampler_name: Sampler name (default: "euler")
        scheduler: Scheduler name (default: "simple")
        denoise: Denoise strength (default: 1.0)
        shift: AuraFlow shift parameter (default: 3)
        strength: CFGNorm strength parameter (default: 1.0)
        output_dir: Directory to save outputs (default: from config)
        request_id: Request identifier (auto-generated if not provided)
        save_tensor: Whether to save tensor to file (default: True)
    
    Returns:
        dict: {
            "status": "success" | "error",
            "request_id": str,
            "sampled_latent_file_path": str | None,
            "sampled_latent_shape": list | None,
            "sampled_latent_tensor": torch.Tensor | None,
            "error_message": str | None,
            "metadata": dict
        }
    """
    start_time = time.time()
    
    if request_id is None:
        request_id = generate_request_id()
    
    if unet_model_name is None:
        unet_model_name = Config.unet_model_name
    
    if lora_model_name is None:
        lora_model_name = Config.lora_model_name
    
    if output_dir is None:
        output_dir = Config.output_dir
    
    if seed is None:
        seed = random.randint(1, 2**64)
    
    try:
        # Setup ComfyUI
        setup_comfyui()
        
        # Import ComfyUI nodes
        from nodes import UNETLoader, LoraLoaderModelOnly, KSampler
        from nodes import NODE_CLASS_MAPPINGS
        
        # Load UNET model
        unet_model_path = Config.get_unet_model_path()
        if not unet_model_path.exists():
            raise UNETModelNotFoundError(f"UNET model not found: {unet_model_path}")
        
        unetloader = UNETLoader()
        unet_output = unetloader.load_unet(
            unet_name=unet_model_name,
            weight_dtype="default"
        )
        unet_model = get_value_at_index(unet_output, 0)
        
        # Load LoRA model and apply to UNET
        lora_model_path = Config.get_lora_model_path()
        if not lora_model_path.exists():
            raise LoRAModelNotFoundError(f"LoRA model not found: {lora_model_path}")
        
        loraloadermodelonly = LoraLoaderModelOnly()
        lora_output = loraloadermodelonly.load_lora_model_only(
            lora_name=lora_model_name,
            strength_model=lora_strength,
            model=unet_model
        )
        lora_model = get_value_at_index(lora_output, 0)
        
        # Apply ModelSamplingAuraFlow
        if "ModelSamplingAuraFlow" not in NODE_CLASS_MAPPINGS:
            raise SamplingFailedError("ModelSamplingAuraFlow node not found in custom nodes")
        
        modelsamplingauraflow = NODE_CLASS_MAPPINGS["ModelSamplingAuraFlow"]()
        auraflow_output = modelsamplingauraflow.patch_aura(
            shift=shift,
            model=lora_model
        )
        auraflow_model = get_value_at_index(auraflow_output, 0)
        
        # Apply CFGNorm
        if "CFGNorm" not in NODE_CLASS_MAPPINGS:
            raise SamplingFailedError("CFGNorm node not found in custom nodes")
        
        cfgnorm = NODE_CLASS_MAPPINGS["CFGNorm"]()
        cfgnorm_output = cfgnorm.EXECUTE_NORMALIZED(
            strength=strength,
            model=auraflow_model
        )
        final_model = get_value_at_index(cfgnorm_output, 0)
        
        # Prepare inputs for sampler
        positive_cond = prepare_conditioning(positive_encoding)
        negative_cond = prepare_conditioning(negative_encoding)
        latent_img = prepare_latent_image(latent_image)
        
        # Run KSampler
        ksampler = KSampler()
        sampler_output = ksampler.sample(
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            denoise=denoise,
            model=final_model,
            positive=positive_cond,
            negative=negative_cond,
            latent_image=latent_img
        )
        
        sampled_latent_raw = get_value_at_index(sampler_output, 0)
        
        # Extract tensor from sampled latent output (might be dict with "samples" key)
        sampled_latent = sampled_latent_raw
        if isinstance(sampled_latent, dict):
            if "samples" in sampled_latent:
                sampled_latent = sampled_latent["samples"]
            elif "latent" in sampled_latent:
                sampled_latent = sampled_latent["latent"]
            elif len(sampled_latent) == 1:
                sampled_latent = list(sampled_latent.values())[0]
        
        if isinstance(sampled_latent, (list, tuple)):
            sampled_latent = sampled_latent[0]
        
        # Ensure it's a tensor
        if not isinstance(sampled_latent, torch.Tensor):
            raise SamplingFailedError(f"Expected tensor, got {type(sampled_latent)}: {sampled_latent}")
        
        # Get sampled latent shape
        sampled_latent_shape = list(sampled_latent.shape) if hasattr(sampled_latent, 'shape') else None
        
        # Save sampled latent tensor
        sampled_latent_file_path = None
        if save_tensor:
            output_dir_obj = ensure_directory_exists(Path(output_dir))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sampled_filename = f"sampled_latent_{request_id}_{timestamp}.pt"
            sampled_latent_file_path = output_dir_obj / sampled_filename
            
            # Save tensor
            torch.save(sampled_latent, sampled_latent_file_path)
            sampled_latent_file_path = str(sampled_latent_file_path)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        metadata = {
            "sampled_latent_shape": sampled_latent_shape,
            "unet_model_name": unet_model_name,
            "lora_model_name": lora_model_name,
            "lora_strength": lora_strength,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "denoise": denoise,
            "shift": shift,
            "strength": strength,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        result = {
            "status": "success",
            "request_id": request_id,
            "sampled_latent_file_path": sampled_latent_file_path,
            "sampled_latent_shape": sampled_latent_shape,
            "metadata": metadata
        }
        
        # Always include tensor in result (for testing/comparison)
        # Also include in dict format for decoder compatibility
        result["sampled_latent_tensor"] = sampled_latent
        result["sampled_latent_dict"] = {"samples": sampled_latent}  # For decoder
        
        return result
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        error_code = type(e).__name__
        error_message = str(e)
        
        return {
            "status": "error",
            "request_id": request_id,
            "error_code": error_code,
            "error_message": error_message,
            "metadata": {
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

