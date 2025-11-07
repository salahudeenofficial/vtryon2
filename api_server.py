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
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import mask.py function
from mask import masked_image

# Add current directory to path for workflow_script_serial
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="Virtual Try-On API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary directories
TEMP_DIR = Path(tempfile.gettempdir()) / "tryon_api"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Input directory for ComfyUI
INPUT_DIR = Path("input")
INPUT_DIR.mkdir(exist_ok=True)

# Output directory for ComfyUI
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def run_workflow_serial(masked_person_path: str, prompt: str, output_filename: str = "tryon_output") -> str:
    """
    Run the workflow_script_serial.py workflow with given parameters.
    
    Args:
        masked_person_path: Path to masked person image
        prompt: Text prompt for the workflow
        output_filename: Base name for output file
    
    Returns:
        Path to the generated output image
    """
    import torch
    from workflow_script_serial import (
        import_custom_nodes_minimal,
        get_value_at_index
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
    
    # Load custom nodes
    import_custom_nodes_minimal()
    
    # Copy masked person image to input directory
    masked_person_filename = "masked_person.png"
    masked_person_input_path = INPUT_DIR / masked_person_filename
    shutil.copy2(masked_person_path, masked_person_input_path)
    
    # Ensure cloth.png exists in input directory
    # (It should have been saved there by the API endpoint before calling this function)
    cloth_path = INPUT_DIR / "cloth.png"
    if not cloth_path.exists():
        raise FileNotFoundError("cloth.png not found in input directory. The cloth image should be uploaded via the API.")
    
    with torch.inference_mode():
        # Load models
        unetloader = UNETLoader()
        unetloader_37 = unetloader.load_unet(
            unet_name="qwen_image_edit_2509_fp8_e4m3fn.safetensors",
            weight_dtype="default",
        )

        cliploader = CLIPLoader()
        cliploader_38 = cliploader.load_clip(
            clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors",
            type="qwen_image",
            device="default",
        )

        vaeloader = VAELoader()
        vaeloader_39 = vaeloader.load_vae(vae_name="qwen_image_vae.safetensors")

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
            vae=get_value_at_index(vaeloader_39, 0),
        )

        # Load LoRA
        loraloadermodelonly = LoraLoaderModelOnly()
        loraloadermodelonly_89 = loraloadermodelonly.load_lora_model_only(
            lora_name="Qwen-Image-Lightning-4steps-V2.0.safetensors",
            strength_model=1,
            model=get_value_at_index(unetloader_37, 0),
        )

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
            clip=get_value_at_index(cliploader_38, 0),
            vae=get_value_at_index(vaeloader_39, 0),
            image1=get_value_at_index(imagescaletototalpixels_93, 0),
            image2=get_value_at_index(loadimage_106, 0),
        )

        # Negative prompt (empty)
        textencodeqwenimageeditplus_110 = textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
            prompt="",
            clip=get_value_at_index(cliploader_38, 0),
            vae=get_value_at_index(vaeloader_39, 0),
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
            vae=get_value_at_index(vaeloader_39, 0),
        )

        # Save image
        saveimage_60 = saveimage.save_images(
            filename_prefix=output_filename,
            images=get_value_at_index(vaedecode_8, 0),
        )
        
        # Get the saved image path
        # SaveImage returns a dict with UI info, we need to find the actual file
        # The image is saved in the output directory with the filename_prefix
        # Find the most recent file with the prefix
        output_files = sorted(OUTPUT_DIR.glob(f"{output_filename}*.png"), key=os.path.getmtime, reverse=True)
        if output_files:
            return str(output_files[0])
        else:
            raise RuntimeError("Failed to save output image")


@app.post("/tryon_extracted")
async def tryon_extracted(
    image: UploadFile = File(..., description="Input person image"),
    cloth: UploadFile = File(None, description="Cloth/garment image to try on (optional, falls back to input/cloth.png)"),
    mask_type: str = Form(..., description="Mask type: upper_body, lower_body, or other"),
    prompt: str = Form(..., description="Text prompt for virtual try-on")
):
    """
    Virtual try-on endpoint.
    
    Process:
    1. Save uploaded image temporarily
    2. Call masked_image() to create masked person image
    3. Run workflow_script_serial.py with masked image and prompt
    4. Return the generated image
    """
    print(f"\n{'='*60}")
    print(f"📥 Received request: /tryon_extracted")
    print(f"   mask_type: {mask_type}")
    print(f"   prompt: {prompt[:50]}..." if len(prompt) > 50 else f"   prompt: {prompt}")
    print(f"{'='*60}\n")
    
    # Validate mask_type
    valid_mask_types = ['upper_body', 'lower_body', 'other']
    if mask_type not in valid_mask_types:
        raise HTTPException(
            status_code=400,
            detail=f"mask_type must be one of {valid_mask_types}, got '{mask_type}'"
        )
    
    # Create temporary files for uploaded images
    temp_input_path = None
    temp_masked_path = None
    temp_cloth_path = None
    
    try:
        print("💾 Saving uploaded images...")
        # Save uploaded person image to temporary file
        temp_input_path = TEMP_DIR / f"input_{os.urandom(8).hex()}.png"
        with open(temp_input_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        print(f"✓ Person image saved to: {temp_input_path}")
        
        # Handle cloth image (uploaded or use existing)
        temp_cloth_path = INPUT_DIR / "cloth.png"
        if cloth and cloth.filename:
            # Save uploaded cloth image to input directory
            with open(temp_cloth_path, "wb") as f:
                shutil.copyfileobj(cloth.file, f)
            print(f"✓ Cloth image uploaded and saved to: {temp_cloth_path}")
        else:
            # Check if cloth.png already exists in input directory
            if not temp_cloth_path.exists():
                error_msg = f"cloth.png not found in {INPUT_DIR.absolute()}. Please either upload a cloth image or ensure cloth.png exists in the input directory."
                print(f"❌ {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)
            print(f"✓ Using existing cloth image: {temp_cloth_path}")
        
        # Call masked_image function
        print(f"🎭 Creating masked image (mask_type: {mask_type})...")
        temp_masked_path = TEMP_DIR / f"masked_{os.urandom(8).hex()}.png"
        masked_image_path = masked_image(
            mask_type=mask_type,
            imagepath=str(temp_input_path),
            output_path=str(temp_masked_path),
            width=576,
            height=768,
            device_index=0
        )
        print(f"✓ Masked image created: {masked_image_path}")
        
        # Run workflow (cloth.png is now in input directory from above)
        print(f"🔄 Running workflow with prompt...")
        output_filename = f"tryon_{os.urandom(8).hex()}"
        output_image_path = run_workflow_serial(
            masked_person_path=masked_image_path,
            prompt=prompt,
            output_filename=output_filename
        )
        print(f"✓ Workflow completed. Output: {output_image_path}")
        
        # Return the generated image
        if not Path(output_image_path).exists():
            error_msg = f"Generated image file not found: {output_image_path}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"✅ Success! Returning image: {output_image_path}")
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
        if temp_input_path and temp_input_path.exists():
            temp_input_path.unlink()
        if temp_masked_path and temp_masked_path.exists():
            temp_masked_path.unlink()
        # Note: cloth.png is kept in input/ directory for potential reuse
        # Uncomment below if you want to clean it up after each request:
        # if temp_cloth_path and temp_cloth_path.exists():
        #     temp_cloth_path.unlink()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

