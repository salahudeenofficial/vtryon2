"""
FastAPI server for virtual try-on service.

Endpoint: POST /tryon_extracted
- Receives: image file, mask_type (upper_body/lower_body/other), prompt
- Calls: masked_image() from mask.py
- Calls: workflow_script_serial.py with masked image and prompt
- Returns: generated image
"""
import os
import sys
import tempfile
import shutil
import time
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import mask.py function
from mask import masked_image

# Import model cache for preloading models
from model_cache import load_models_once, get_cached_model, is_models_loaded

# Add current directory to path for workflow_script_serial
sys.path.insert(0, str(Path(__file__).parent))

# Temporary directories
TEMP_DIR = Path(tempfile.gettempdir()) / "tryon_api"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Input directory for ComfyUI
INPUT_DIR = Path("input")
INPUT_DIR.mkdir(exist_ok=True)

# Output directory for ComfyUI
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Loads models at startup and keeps them in memory.
    """
    # Startup: Load models
    logger.info("=" * 60)
    logger.info("FastAPI Startup: Loading models into CPU memory...")
    logger.info("=" * 60)
    try:
        load_models_once()
        logger.info("=" * 60)
        logger.info("✓ All models loaded and ready for requests!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Failed to load models at startup: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    
    yield
    
    # Shutdown: Cleanup (optional)
    logger.info("FastAPI Shutdown: Cleaning up...")


app = FastAPI(
    title="Virtual Try-On API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_workflow_serial(masked_person_path: str, prompt: str, output_filename: str = "tryon_output") -> str:
    """
    Run the workflow_script_serial.py workflow with given parameters.
    Uses pre-loaded cached models from startup.
    
    Args:
        masked_person_path: Path to masked person image
        prompt: Text prompt for the workflow
        output_filename: Base name for output file
    
    Returns:
        Path to the generated output image
    """
    import torch
    from workflow_script_serial import get_value_at_index
    from nodes import (
        SaveImage,
        VAEEncode,
        LoadImage,
        KSampler,
        NODE_CLASS_MAPPINGS,
        VAEDecode,
    )
    
    # Ensure models are loaded
    if not is_models_loaded():
        raise RuntimeError("Models not loaded. Server may not have initialized properly.")
    
    # Get cached models (loaded on CPU at startup)
    # These are full loader return values, extract when needed
    unet_model = get_cached_model("unet")
    clip_model = get_cached_model("clip")
    vae_model = get_cached_model("vae")
    lora_model = get_cached_model("lora")
    
    # Copy masked person image to input directory
    masked_person_filename = "masked_person.png"
    masked_person_input_path = INPUT_DIR / masked_person_filename
    shutil.copy2(masked_person_path, masked_person_input_path)
    
    # Ensure cloth.png exists (or use a default)
    # For now, we'll assume cloth.png is already in input directory
    # In a full implementation, you might want to accept cloth image as well
    cloth_path = INPUT_DIR / "cloth.png"
    if not cloth_path.exists():
        # Create a placeholder or raise error
        raise FileNotFoundError("cloth.png not found in input directory. Please provide a cloth image.")
    
    with torch.inference_mode():
        # Models will be automatically loaded to GPU by ComfyUI when needed
        # No need to explicitly load them here - ComfyUI's model management handles it
        # This ensures models stay on CPU until actually needed, saving GPU memory

        # Load masked person image
        loadimage = LoadImage()
        loadimage_78 = loadimage.load_image(image=masked_person_filename)

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
            vae=get_value_at_index(vae_model, 0),  # Use cached VAE model
        )

        # LoRA is already loaded and cached
        loraloadermodelonly_89 = lora_model  # Use cached LoRA model

        # Load cloth image
        loadimage_106 = loadimage.load_image(image="cloth.png")

        # Empty latent
        emptysd3latentimage = NODE_CLASS_MAPPINGS["EmptySD3LatentImage"]()
        emptysd3latentimage_112 = emptysd3latentimage.EXECUTE_NORMALIZED(
            width=1024, height=1024, batch_size=1
        )

        # Model sampling and CFG
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
            clip=get_value_at_index(clip_model, 0),  # Use cached CLIP model
            vae=get_value_at_index(vae_model, 0),  # Use cached VAE model
            image1=get_value_at_index(imagescaletototalpixels_93, 0),
            image2=get_value_at_index(loadimage_106, 0),
        )

        # Negative prompt (empty)
        textencodeqwenimageeditplus_110 = textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
            prompt="",
            clip=get_value_at_index(clip_model, 0),  # Use cached CLIP model
            vae=get_value_at_index(vae_model, 0),  # Use cached VAE model
            image1=get_value_at_index(imagescaletototalpixels_93, 0),
            image2=get_value_at_index(loadimage_106, 0),
        )

        # Sample
        import random
        ksampler_3 = ksampler.sample(
            seed=random.randint(1, 2**64),
            steps=4,
            cfg=1,
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
            vae=get_value_at_index(vae_model, 0),  # Use cached VAE model
        )

        # Save image
        saveimage_result = saveimage.save_images(
            filename_prefix=output_filename,
            images=get_value_at_index(vaedecode_8, 0),
        )
        
        # Get the saved image path from the return value
        # SaveImage returns: { "ui": { "images": [{"filename": "...", "subfolder": "...", "type": "..."}] } }
        try:
            saved_images = saveimage_result.get("ui", {}).get("images", [])
            if not saved_images:
                raise RuntimeError("SaveImage did not return image information")
            
            # Get the first saved image (usually only one)
            first_image = saved_images[0]
            saved_filename = first_image.get("filename")
            subfolder = first_image.get("subfolder", "")
            
            if not saved_filename:
                raise RuntimeError("SaveImage did not return filename")
            
            # Construct full path
            if subfolder:
                output_path = OUTPUT_DIR / subfolder / saved_filename
            else:
                output_path = OUTPUT_DIR / saved_filename
            
            # Verify file exists
            if not output_path.exists():
                raise RuntimeError(f"Saved image file not found: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            # Fallback: try to find the file by pattern (less reliable)
            print(f"Warning: Could not extract filename from SaveImage result: {e}")
            output_files = sorted(OUTPUT_DIR.glob(f"{output_filename}*.png"), key=os.path.getmtime, reverse=True)
            if output_files:
                return str(output_files[0])
            else:
                raise RuntimeError("Failed to save output image")


@app.post("/tryon_extracted")
async def tryon_extracted(
    image: UploadFile = File(..., description="Input person image"),
    cloth: UploadFile = File(..., description="Cloth/garment image to try on"),
    mask_type: str = Form(..., description="Mask type: upper_body, lower_body, or other"),
    prompt: Optional[str] = Form(None, description="Text prompt for virtual try-on (ignored - prompt is hardcoded based on mask_type)")
):
    """
    Virtual try-on endpoint.
    
    Process:
    1. Save uploaded image temporarily
    2. Call masked_image() to create masked person image
    3. Run workflow_script_serial.py with masked image and hardcoded prompt (based on mask_type)
    4. Return the generated image
    
    Note: Prompt is automatically set based on mask_type:
    - upper_body/lower_body: "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
    - other: "tryon the garment in the Picture 2 on the person in Picture 1 .Dont't change the style and appearence of the garment and keep the garment look identical. "
    """
    # Validate mask_type
    valid_mask_types = ['upper_body', 'lower_body', 'other']
    if mask_type not in valid_mask_types:
        raise HTTPException(
            status_code=400,
            detail=f"mask_type must be one of {valid_mask_types}, got '{mask_type}'"
        )
    
    # Hardcode prompt based on mask_type
    if mask_type in ['upper_body', 'lower_body']:
        prompt = "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
    else:  # mask_type == 'other'
        prompt = "tryon the garment in the Picture 2 on the person in Picture 1 .Dont't change the style and appearence of the garment and keep the garment look identical. "
    
    # Record start time for request timing
    start_time = time.perf_counter()
    
    # Create temporary file for uploaded image
    temp_input_path = None
    temp_masked_path = None
    
    try:
        # Save uploaded person image to temporary file
        temp_input_path = TEMP_DIR / f"input_{os.urandom(8).hex()}.png"
        with open(temp_input_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        
        # Save uploaded cloth image to input directory
        cloth_path = INPUT_DIR / "cloth.png"
        with open(cloth_path, "wb") as f:
            shutil.copyfileobj(cloth.file, f)
        
        # Call masked_image function
        temp_masked_path = TEMP_DIR / f"masked_{os.urandom(8).hex()}.png"
        masked_image_path = masked_image(
            mask_type=mask_type,
            imagepath=str(temp_input_path),
            output_path=str(temp_masked_path),
            width=576,
            height=768,
            device_index=0
        )
        
        # Run workflow
        output_filename = f"tryon_{os.urandom(8).hex()}"
        output_image_path = run_workflow_serial(
            masked_person_path=masked_image_path,
            prompt=prompt,
            output_filename=output_filename
        )
        
        # Return the generated image
        if not Path(output_image_path).exists():
            raise HTTPException(status_code=500, detail="Generated image file not found")
        
        return FileResponse(
            output_image_path,
            media_type="image/png",
            filename=Path(output_image_path).name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    
    finally:
        # Calculate and log request processing time
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logger.info(f"Request completed - mask_type: {mask_type}, time_taken: {elapsed_time:.2f} seconds ({elapsed_time*1000:.2f} ms)")
        
        # Clean up temporary files
        if temp_input_path and temp_input_path.exists():
            temp_input_path.unlink()
        if temp_masked_path and temp_masked_path.exists():
            temp_masked_path.unlink()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

