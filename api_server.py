"""
FastAPI server for Qwen Image Edit workflow.

Endpoint: POST /tryon
- Receives: masked_person_image (file), cloth_image (file), prompt (text)
- Runs: workflow_script_serial.py logic
- Returns: generated result image
"""
import os
import sys
import shutil
import asyncio
import threading
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for workflow_script_serial
sys.path.insert(0, str(Path(__file__).parent))

# Import model cache
from model_cache import load_models_once, get_cached_model, is_models_loaded


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
    title="Qwen Image Edit API",
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

# Input and output directories
INPUT_DIR = Path("input")
INPUT_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def import_custom_nodes_minimal() -> None:
    """
    Minimal custom node loading that works both standalone and within an existing event loop.
    This is lighter than the full server setup but still requires async execution.
    """
    import asyncio
    from nodes import init_extra_nodes

    # Check if there's a running event loop (e.g., from FastAPI)
    try:
        loop = asyncio.get_running_loop()
        # If we're in an existing event loop, we need to run it differently
        # Use asyncio.ensure_future or create_task, but we need to wait for it
        # Since this is a synchronous function, we'll use run_until_complete on a new thread
        import concurrent.futures
        import threading

        def run_in_thread():
            # Create a new event loop in this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(init_extra_nodes(init_custom_nodes=True, init_api_nodes=False))
            finally:
                new_loop.close()

        # Run in a separate thread to avoid event loop conflicts
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()

    except RuntimeError:
        # No running event loop, safe to use asyncio.run()
        asyncio.run(init_extra_nodes(init_custom_nodes=True, init_api_nodes=False))


def get_value_at_index(obj, index: int):
    """Returns the value at the given index of a sequence or mapping."""
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def run_workflow(
    masked_person_image_path: str,
    cloth_image_path: str,
    prompt: str,
    output_filename: str = "qwen_output",
    seed: Optional[int] = None
) -> str:
    """
    Run the Qwen Image Edit workflow.
    
    Args:
        masked_person_image_path: Path to masked person image
        cloth_image_path: Path to cloth image
        prompt: Text prompt for the workflow
        output_filename: Base name for output file
        seed: Optional random seed for reproducibility
    
    Returns:
        Path to the generated output image
    """
    import torch
    import random
    from workflow_script_serial import (
        add_comfyui_directory_to_sys_path,
        add_extra_model_paths,
    )
    from nodes import (
        UNETLoader,
        CLIPLoader,
        SaveImage,
        VAEEncode,
        LoadImage,
        KSampler,
        VAELoader,
        NODE_CLASS_MAPPINGS,
        VAEDecode,
        LoraLoaderModelOnly,
    )
    
    # Setup ComfyUI paths
    add_comfyui_directory_to_sys_path()
    add_extra_model_paths()
    
    # Load custom nodes
    import_custom_nodes_minimal()
    
    # Copy images to input directory
    masked_person_input_path = INPUT_DIR / "masked_person.png"
    cloth_input_path = INPUT_DIR / "cloth.png"
    
    shutil.copy2(masked_person_image_path, masked_person_input_path)
    shutil.copy2(cloth_image_path, cloth_input_path)
    
    # Check if models are loaded, if not load them (fallback)
    if not is_models_loaded():
        logger.warning("Models not loaded at startup, loading now (this should not happen)")
        load_models_once()
    
    # Get cached models (already loaded and in CPU memory)
    try:
        unet_model = get_cached_model("unet")
        clip_model = get_cached_model("clip")
        vae_model = get_cached_model("vae")
        lora_model = get_cached_model("lora")
    except Exception as e:
        logger.error(f"Error getting cached models: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to get cached models: {e}")
    
    with torch.inference_mode():
        # Models will be automatically loaded to GPU by ComfyUI when needed
        # No need to explicitly load them here - ComfyUI's model management handles it
        # This ensures models stay on CPU until actually needed, saving GPU memory

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
            vae=get_value_at_index(vae_model, 0),  # Use cached VAE model
        )

        # LoRA is already loaded and cached
        loraloadermodelonly_89 = lora_model  # Use cached LoRA model

        # Load cloth image
        loadimage_106 = loadimage.load_image(image="cloth.png")

        # Empty latent (not used in this workflow but kept for compatibility)
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
            shift=3, model=get_value_at_index(loraloadermodelonly_89, 0)  # Use cached LoRA model
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
        if seed is None:
            seed = random.randint(1, 2**64)
        
        ksampler_3 = ksampler.sample(
            seed=seed,
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


@app.post("/tryon")
async def tryon(
    masked_person_image: UploadFile = File(..., description="Masked person image"),
    cloth_image: UploadFile = File(..., description="Cloth/garment image"),
    prompt: str = Form(..., description="Text prompt for virtual try-on"),
    seed: Optional[int] = Form(None, description="Optional random seed for reproducibility")
):
    """
    Virtual try-on endpoint.
    
    Process:
    1. Save uploaded images temporarily
    2. Run Qwen Image Edit workflow with masked person image, cloth image, and prompt
    3. Return the generated image
    
    Args:
        masked_person_image: Uploaded masked person image file
        cloth_image: Uploaded cloth/garment image file
        prompt: Text prompt for the workflow
        seed: Optional random seed for reproducibility
    
    Returns:
        Generated result image file
    """
    import tempfile
    
    temp_masked_path = None
    temp_cloth_path = None
    
    try:
        # Save uploaded images to temporary files
        temp_masked_path = Path(tempfile.gettempdir()) / f"masked_{os.urandom(8).hex()}.png"
        temp_cloth_path = Path(tempfile.gettempdir()) / f"cloth_{os.urandom(8).hex()}.png"
        
        with open(temp_masked_path, "wb") as f:
            shutil.copyfileobj(masked_person_image.file, f)
        
        with open(temp_cloth_path, "wb") as f:
            shutil.copyfileobj(cloth_image.file, f)
        
        # Generate unique output filename
        output_filename = f"qwen_{os.urandom(8).hex()}"
        
        # Run workflow
        output_image_path = run_workflow(
            masked_person_image_path=str(temp_masked_path),
            cloth_image_path=str(temp_cloth_path),
            prompt=prompt,
            output_filename=output_filename,
            seed=seed
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
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error processing request: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    
    finally:
        # Clean up temporary files
        if temp_masked_path and temp_masked_path.exists():
            temp_masked_path.unlink()
        if temp_cloth_path and temp_cloth_path.exists():
            temp_cloth_path.unlink()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "qwen_image_edit"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
