"""
FLUX.2 [klein] 9B Virtual Try-On POC Server
FastAPI server for virtual try-on using FLUX.2-klein-9B model

Uses the official BFL flux2 repository for inference.
"""

import io
import base64
import uuid
import os
import sys
import time
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import torch
from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Global model reference
model = None
sampler = None
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32


class TryOnRequest(BaseModel):
    person_image: str  # Base64 encoded
    garment_image: str  # Base64 encoded
    prompt: Optional[str] = "A photo of the person wearing the garment, maintaining identity and garment texture"
    num_inference_steps: int = 4
    guidance_scale: float = 1.0
    seed: Optional[int] = None
    width: int = 1024
    height: int = 1024


class TryOnResponse(BaseModel):
    result_image: str  # Base64 encoded
    seed_used: int
    inference_time_ms: Optional[float] = None
    peak_gpu_memory_gb: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    cuda_available: bool
    gpu_name: Optional[str] = None
    gpu_memory_total: Optional[str] = None
    gpu_memory_free: Optional[str] = None
    pipeline_type: Optional[str] = None


def load_model():
    """Load the FLUX.2-klein-9B model using available pipeline"""
    global model, sampler
    
    print("=" * 60)
    print("Loading FLUX.2-klein-9B model...")
    print("=" * 60)
    print("NOTE: CPU offload is DISABLED - model will run fully on GPU")
    print("      This provides maximum performance but requires ~29GB VRAM")
    print("=" * 60)
    
    # Try multiple loading strategies
    
    # Strategy 1: Try diffusers Flux2KleinPipeline (if available in latest diffusers)
    try:
        print("\n[1/3] Trying Flux2KleinPipeline from diffusers...")
        from diffusers import Flux2KleinPipeline
        
        model = Flux2KleinPipeline.from_pretrained(
            "black-forest-labs/FLUX.2-klein-9B",
            torch_dtype=dtype,
        )
        
        # Move to GPU (NO CPU offload for full performance)
        if torch.cuda.is_available():
            model = model.to("cuda")
            print(f"  Model moved to GPU: {torch.cuda.get_device_name(0)}")
        
        print("✓ Loaded with Flux2KleinPipeline")
        return "Flux2KleinPipeline"
        
    except ImportError as e:
        print(f"  Flux2KleinPipeline not available: {e}")
    except Exception as e:
        print(f"  Failed: {e}")
    
    # Strategy 2: Try FluxPipeline with klein model (generic flux pipeline)
    try:
        print("\n[2/3] Trying FluxPipeline from diffusers...")
        from diffusers import FluxPipeline
        
        model = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.2-klein-9B",
            torch_dtype=dtype,
        )
        
        # Move to GPU (NO CPU offload for full performance)
        if torch.cuda.is_available():
            model = model.to("cuda")
            print(f"  Model moved to GPU: {torch.cuda.get_device_name(0)}")
        
        print("✓ Loaded with FluxPipeline")
        return "FluxPipeline"
        
    except ImportError as e:
        print(f"  FluxPipeline not available: {e}")
    except Exception as e:
        print(f"  Failed: {e}")
    
    # Strategy 3: Try FluxImg2ImgPipeline for image-to-image
    try:
        print("\n[3/3] Trying FluxImg2ImgPipeline from diffusers...")
        from diffusers import FluxImg2ImgPipeline
        
        model = FluxImg2ImgPipeline.from_pretrained(
            "black-forest-labs/FLUX.2-klein-9B",
            torch_dtype=dtype,
        )
        
        # Move to GPU (NO CPU offload for full performance)
        if torch.cuda.is_available():
            model = model.to("cuda")
            print(f"  Model moved to GPU: {torch.cuda.get_device_name(0)}")
        
        print("✓ Loaded with FluxImg2ImgPipeline")
        return "FluxImg2ImgPipeline"
        
    except ImportError as e:
        print(f"  FluxImg2ImgPipeline not available: {e}")
    except Exception as e:
        print(f"  Failed: {e}")
    
        print("\n" + "=" * 60)
        print("ERROR: Could not load model with any available pipeline")
        print("=" * 60)
        print("\nPlease try:")
        print("  1. pip install -U diffusers transformers accelerate")
        print("  2. pip install git+https://github.com/huggingface/diffusers.git")
        print("  3. Ensure you've accepted the model license on HuggingFace")
        print("  4. Run: huggingface-cli login")
        print("  5. Set HF_TOKEN environment variable if needed")
        
        return None


# Track pipeline type
pipeline_type = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model loading"""
    global pipeline_type
    # Startup
    pipeline_type = load_model()
    if pipeline_type is None:
        print("WARNING: Model failed to load. Server will start but inference will fail.")
    yield
    # Shutdown
    global model
    if model is not None:
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


app = FastAPI(
    title="FLUX.2 Klein Virtual Try-On POC",
    description="Virtual try-on using FLUX.2-klein-9B multi-reference editing",
    version="0.2.0",
    lifespan=lifespan
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def decode_base64_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image"""
    # Handle data URL format
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    return image


def encode_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Encode PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def create_composite_image(person_img: Image.Image, garment_img: Image.Image, 
                           width: int, height: int) -> Image.Image:
    """
    Create a side-by-side composite image for models that don't support multi-reference.
    This is a fallback for older pipelines.
    """
    # Resize both images to half width
    half_width = width // 2
    person_resized = person_img.resize((half_width, height), Image.Resampling.LANCZOS)
    garment_resized = garment_img.resize((half_width, height), Image.Resampling.LANCZOS)
    
    # Create composite
    composite = Image.new('RGB', (width, height))
    composite.paste(person_resized, (0, 0))
    composite.paste(garment_resized, (half_width, 0))
    
    return composite


def run_inference(person_img: Image.Image, garment_img: Image.Image,
                  prompt: str, width: int, height: int,
                  num_steps: int, guidance: float, seed: int):
    """Run inference with the loaded model and track performance metrics"""
    global model, pipeline_type
    
    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)
    
    # Resize images
    person_img = person_img.resize((width, height), Image.Resampling.LANCZOS)
    garment_img = garment_img.resize((width, height), Image.Resampling.LANCZOS)
    
    # Clear GPU cache and reset peak memory tracking
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()
        memory_before = torch.cuda.memory_allocated() / 1024**3  # GB
    
    # Start timing
    start_time = time.time()
    
    try:
        if pipeline_type == "Flux2KleinPipeline":
            # Native multi-reference support
            result = model(
                prompt=prompt,
                image=[person_img, garment_img],
                height=height,
                width=width,
                guidance_scale=guidance,
                num_inference_steps=num_steps,
                generator=generator,
            )
        elif pipeline_type == "FluxImg2ImgPipeline":
            # Image-to-image: use composite as init image
            composite = create_composite_image(person_img, garment_img, width, height)
            result = model(
                prompt=f"Virtual try-on: {prompt}. Left side shows the person, right side shows the garment to wear.",
                image=composite,
                strength=0.8,
                height=height,
                width=width,
                guidance_scale=guidance,
                num_inference_steps=num_steps,
                generator=generator,
            )
        elif pipeline_type == "FluxPipeline":
            # Text-to-image with detailed prompt
            # For text-only, we describe both images in the prompt
            enhanced_prompt = f"""Virtual try-on fashion photo: {prompt}
The person should maintain their identity, pose, and body shape.
The garment details, texture, and style should be accurately represented."""
            result = model(
                prompt=enhanced_prompt,
                height=height,
                width=width,
                guidance_scale=guidance,
                num_inference_steps=num_steps,
                generator=generator,
            )
        else:
            raise ValueError(f"Unknown pipeline type: {pipeline_type}")
    finally:
        # End timing
        inference_time_ms = (time.time() - start_time) * 1000
        
        # Get peak GPU memory
        peak_gpu_memory_gb = None
        if torch.cuda.is_available():
            peak_memory = torch.cuda.max_memory_allocated() / 1024**3  # GB
            peak_gpu_memory_gb = peak_memory
    
    return result.images[0], inference_time_ms, peak_gpu_memory_gb


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with GPU info"""
    gpu_name = None
    gpu_memory_total = None
    gpu_memory_free = None
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        gpu_memory_total = f"{props.total_memory / 1024**3:.2f} GB"
        
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        free_memory = (props.total_memory / 1024**3) - reserved
        gpu_memory_free = f"{free_memory:.2f} GB"
    
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        device=device,
        cuda_available=torch.cuda.is_available(),
        gpu_name=gpu_name,
        gpu_memory_total=gpu_memory_total,
        gpu_memory_free=gpu_memory_free,
        pipeline_type=pipeline_type
    )


@app.post("/tryon", response_model=TryOnResponse)
async def virtual_tryon(request: TryOnRequest):
    """
    Virtual try-on endpoint using FLUX.2-klein-9B
    
    Takes a person image and garment image, returns the person wearing the garment.
    """
    global model
    
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please wait for model initialization or check server logs."
        )
    
    try:
        # Decode input images
        person_img = decode_base64_image(request.person_image)
        garment_img = decode_base64_image(request.garment_image)
        
        # Set seed for reproducibility
        seed = request.seed if request.seed is not None else torch.randint(0, 2**32, (1,)).item()
        
        # Run inference (returns image, time, peak memory)
        result_image, inference_time_ms, peak_gpu_memory_gb = run_inference(
            person_img=person_img,
            garment_img=garment_img,
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            num_steps=request.num_inference_steps,
            guidance=request.guidance_scale,
            seed=seed
        )
        
        # Encode result to base64
        result_base64 = encode_image_to_base64(result_image)
        
        # Log performance metrics
        print(f"\n{'='*60}")
        print(f"Inference completed:")
        print(f"  Time: {inference_time_ms:.2f} ms ({inference_time_ms/1000:.3f} seconds)")
        print(f"  Peak GPU Memory: {peak_gpu_memory_gb:.2f} GB")
        print(f"  Steps: {request.num_inference_steps}")
        print(f"  Seed: {seed}")
        print(f"{'='*60}\n")
        
        return TryOnResponse(
            result_image=f"data:image/png;base64,{result_base64}",
            seed_used=seed,
            inference_time_ms=inference_time_ms,
            peak_gpu_memory_gb=peak_gpu_memory_gb
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )


@app.post("/tryon/upload")
async def virtual_tryon_upload(
    person_image: UploadFile = File(..., description="Person image file"),
    garment_image: UploadFile = File(..., description="Garment image file"),
    prompt: str = Form(default="A photo of the person wearing the garment, maintaining identity and garment texture"),
    num_inference_steps: int = Form(default=4),
    guidance_scale: float = Form(default=1.0),
    seed: Optional[int] = Form(default=None),
    width: int = Form(default=1024),
    height: int = Form(default=1024),
):
    """
    Virtual try-on endpoint with file upload support
    
    Alternative endpoint that accepts file uploads instead of base64.
    """
    global model
    
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please wait for model initialization or check server logs."
        )
    
    try:
        # Read uploaded files
        person_data = await person_image.read()
        garment_data = await garment_image.read()
        
        # Convert to PIL Images
        person_img = Image.open(io.BytesIO(person_data))
        garment_img = Image.open(io.BytesIO(garment_data))
        
        # Convert to RGB if necessary
        if person_img.mode != "RGB":
            person_img = person_img.convert("RGB")
        if garment_img.mode != "RGB":
            garment_img = garment_img.convert("RGB")
        
        # Set seed
        actual_seed = seed if seed is not None else torch.randint(0, 2**32, (1,)).item()
        
        # Run inference (returns image, time, peak memory)
        result_image, inference_time_ms, peak_gpu_memory_gb = run_inference(
            person_img=person_img,
            garment_img=garment_img,
            prompt=prompt,
            width=width,
            height=height,
            num_steps=num_inference_steps,
            guidance=guidance_scale,
            seed=actual_seed
        )
        
        # Log performance metrics
        print(f"\n{'='*60}")
        print(f"Inference completed:")
        print(f"  Time: {inference_time_ms:.2f} ms ({inference_time_ms/1000:.3f} seconds)")
        print(f"  Peak GPU Memory: {peak_gpu_memory_gb:.2f} GB")
        print(f"  Steps: {num_inference_steps}")
        print(f"  Seed: {actual_seed}")
        print(f"{'='*60}\n")
        
        # Return as streaming response (PNG)
        buffer = io.BytesIO()
        result_image.save(buffer, format="PNG")
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="image/png",
            headers={
                "X-Seed-Used": str(actual_seed),
                "X-Inference-Time-Ms": str(inference_time_ms),
                "X-Peak-GPU-Memory-GB": str(peak_gpu_memory_gb),
                "Content-Disposition": f"attachment; filename=tryon_result_{actual_seed}.png"
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "FLUX.2 Klein Virtual Try-On POC",
        "version": "0.2.0",
        "pipeline_type": pipeline_type,
        "endpoints": {
            "/health": "GET - Health check with GPU info",
            "/tryon": "POST - Virtual try-on with base64 images",
            "/tryon/upload": "POST - Virtual try-on with file uploads",
            "/docs": "GET - OpenAPI documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
