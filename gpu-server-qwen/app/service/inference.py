"""
Inference service for running Qwen Image Edit workflow.
Extracts workflow logic from workflow_script_serial.py
"""
import os
import sys
import time
import torch
import random
from pathlib import Path
from typing import Tuple, Optional
import logging

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from model_cache import get_cached_model, is_models_loaded
from workflow_script_serial import (
    add_comfyui_directory_to_sys_path,
    add_extra_model_paths,
    get_value_at_index,
)
from nodes import (
    LoadImage,
    VAEEncode,
    KSampler,
    VAEDecode,
    SaveImage,
    NODE_CLASS_MAPPINGS,
)

logger = logging.getLogger(__name__)


async def run_inference(
    masked_user_image_path: str,
    garment_image_path: str,
    prompt: str,
    output_dir: str = "output",
    seed: Optional[int] = None,
    steps: int = 4,
    cfg: float = 1.0,
) -> Tuple[str, float]:
    """
    Run Qwen Image Edit inference workflow.
    
    Args:
        masked_user_image_path: Path to masked user image
        garment_image_path: Path to garment image
        prompt: Text prompt for the workflow
        output_dir: Output directory for results
        seed: Optional random seed
        steps: Number of sampling steps
        cfg: CFG scale
        
    Returns:
        Tuple of (output_image_path, inference_time_ms)
        
    Raises:
        RuntimeError: If models not loaded or inference fails
    """
    if not is_models_loaded():
        raise RuntimeError("Models not loaded. Call load_models_once() first.")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Start timing
    start_time = time.time()
    
    try:
        # Get cached models
        unet_model = get_cached_model("unet")
        clip_model = get_cached_model("clip")
        vae_model = get_cached_model("vae")
        lora_model = get_cached_model("lora")
        
        # Copy images to input directory (ComfyUI expects them in input/)
        input_dir = Path("input")
        input_dir.mkdir(exist_ok=True)
        
        masked_input_path = input_dir / "masked_person.png"
        garment_input_path = input_dir / "cloth.png"
        
        import shutil
        shutil.copy2(masked_user_image_path, masked_input_path)
        shutil.copy2(garment_image_path, garment_input_path)
        
        with torch.inference_mode():
            # Load masked person image
            loadimage = LoadImage()
            loadimage_78 = loadimage.load_image(image="masked_person.png")
            
            # Scale image
            imagescaletototalpixels = NODE_CLASS_MAPPINGS["ImageScaleToTotalPixels"]()
            imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(
                upscale_method="lanczos",
                megapixels=1,
                image=get_value_at_index(loadimage_78, 0),
            )
            
            # Encode to latent
            vaeencode = VAEEncode()
            vaeencode_88 = vaeencode.encode(
                pixels=get_value_at_index(imagescaletototalpixels_93, 0),
                vae=get_value_at_index(vae_model, 0),
            )
            
            # LoRA is already loaded and cached
            loraloadermodelonly_89 = lora_model
            
            # Load garment image
            loadimage_106 = loadimage.load_image(image="cloth.png")
            
            # Empty latent (not used but kept for compatibility)
            emptysd3latentimage = NODE_CLASS_MAPPINGS["EmptySD3LatentImage"]()
            emptysd3latentimage_112 = emptysd3latentimage.EXECUTE_NORMALIZED(
                width=1024, height=1024, batch_size=1
            )
            
            # Initialize nodes
            modelsamplingauraflow = NODE_CLASS_MAPPINGS["ModelSamplingAuraFlow"]()
            cfgnorm = NODE_CLASS_MAPPINGS["CFGNorm"]()
            textencodeqwenimageeditplus = NODE_CLASS_MAPPINGS["TextEncodeQwenImageEditPlus"]()
            ksampler = KSampler()
            vaedecode = VAEDecode()
            saveimage = SaveImage()
            
            # Apply model sampling
            modelsamplingauraflow_66 = modelsamplingauraflow.patch_aura(
                shift=3, model=get_value_at_index(loraloadermodelonly_89, 0)
            )
            
            cfgnorm_75 = cfgnorm.EXECUTE_NORMALIZED(
                strength=1, model=get_value_at_index(modelsamplingauraflow_66, 0)
            )
            
            # Encode prompts with images
            # Positive prompt
            textencodeqwenimageeditplus_111 = textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
                prompt=prompt,
                clip=get_value_at_index(clip_model, 0),
                vae=get_value_at_index(vae_model, 0),
                image1=get_value_at_index(imagescaletototalpixels_93, 0),
                image2=get_value_at_index(loadimage_106, 0),
            )
            
            # Negative prompt (empty)
            textencodeqwenimageeditplus_110 = textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
                prompt="",
                clip=get_value_at_index(clip_model, 0),
                vae=get_value_at_index(vae_model, 0),
                image1=get_value_at_index(imagescaletototalpixels_93, 0),
                image2=get_value_at_index(loadimage_106, 0),
            )
            
            # Sample
            if seed is None:
                seed = random.randint(1, 2**64)
            
            ksampler_3 = ksampler.sample(
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler_name="euler",
                scheduler="simple",
                denoise=1,
                model=get_value_at_index(cfgnorm_75, 0),
                positive=get_value_at_index(textencodeqwenimageeditplus_111, 0),
                negative=get_value_at_index(textencodeqwenimageeditplus_110, 0),
                latent_image=get_value_at_index(vaeencode_88, 0),
            )
            
            # Decode
            vaedecode_8 = vaedecode.decode(
                samples=get_value_at_index(ksampler_3, 0),
                vae=get_value_at_index(vae_model, 0),
            )
            
            # Save image
            output_filename = f"qwen_{os.urandom(8).hex()}"
            saveimage_result = saveimage.save_images(
                filename_prefix=output_filename,
                images=get_value_at_index(vaedecode_8, 0),
            )
            
            # Get the saved image path
            try:
                saved_images = saveimage_result.get("ui", {}).get("images", [])
                if not saved_images:
                    raise RuntimeError("SaveImage did not return image information")
                
                first_image = saved_images[0]
                saved_filename = first_image.get("filename")
                subfolder = first_image.get("subfolder", "")
                
                if not saved_filename:
                    raise RuntimeError("SaveImage did not return filename")
                
                # Construct full path
                if subfolder:
                    output_path = Path(output_dir) / subfolder / saved_filename
                else:
                    output_path = Path(output_dir) / saved_filename
                
                if not output_path.exists():
                    raise RuntimeError(f"Saved image file not found: {output_path}")
                
                # Calculate inference time
                inference_time_ms = (time.time() - start_time) * 1000
                
                return str(output_path), inference_time_ms
                
            except Exception as e:
                logger.error(f"Failed to extract output image path: {e}")
                # Fallback: try to find the file by pattern
                output_files = sorted(
                    Path(output_dir).glob(f"{output_filename}*.png"),
                    key=os.path.getmtime,
                    reverse=True
                )
                if output_files:
                    inference_time_ms = (time.time() - start_time) * 1000
                    return str(output_files[0]), inference_time_ms
                else:
                    raise RuntimeError("Failed to save output image")
                    
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        raise RuntimeError(f"Inference failed: {str(e)}") from e

