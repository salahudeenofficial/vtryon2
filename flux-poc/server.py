"""
FLUX.2 [klein] 9B Virtual Try-On POC Server
FastAPI server for virtual try-on using FLUX.2-klein-9B model
"""

import io
import base64
import uuid
import asyncio
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
pipe = None
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


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    cuda_available: bool
    gpu_name: Optional[str] = None
    gpu_memory_total: Optional[str] = None
    gpu_memory_free: Optional[str] = None


def load_model():
    """Load the FLUX.2-klein-9B model"""
    global pipe
    
    print("Loading FLUX.2-klein-9B model...")
    
    try:
        from diffusers import Flux2KleinPipeline
        
        pipe = Flux2KleinPipeline.from_pretrained(
            "black-forest-labs/FLUX.2-klein-9B",
            torch_dtype=dtype,
        )
        
        # Use CPU offload to manage VRAM
        if torch.cuda.is_available():
            pipe.enable_model_cpu_offload()
        
        print(f"Model loaded successfully on {device}")
        return True
        
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Attempting to load with reduced precision...")
        
        try:
            # Try with float16 if bfloat16 fails
            from diffusers import Flux2KleinPipeline
            
            pipe = Flux2KleinPipeline.from_pretrained(
                "black-forest-labs/FLUX.2-klein-9B",
                torch_dtype=torch.float16,
            )
            
            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()
            
            print(f"Model loaded with float16 on {device}")
            return True
            
        except Exception as e2:
            print(f"Failed to load model: {e2}")
            return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model loading"""
    # Startup
    success = load_model()
    if not success:
        print("WARNING: Model failed to load. Server will start but inference will fail.")
    yield
    # Shutdown
    global pipe
    if pipe is not None:
        del pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


app = FastAPI(
    title="FLUX.2 Klein Virtual Try-On POC",
    description="Virtual try-on using FLUX.2-klein-9B multi-reference editing",
    version="0.1.0",
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
        
        free_memory = torch.cuda.memory_reserved(0) - torch.cuda.memory_allocated(0)
        gpu_memory_free = f"{free_memory / 1024**3:.2f} GB"
    
    return HealthResponse(
        status="healthy",
        model_loaded=pipe is not None,
        device=device,
        cuda_available=torch.cuda.is_available(),
        gpu_name=gpu_name,
        gpu_memory_total=gpu_memory_total,
        gpu_memory_free=gpu_memory_free
    )


@app.post("/tryon", response_model=TryOnResponse)
async def virtual_tryon(request: TryOnRequest):
    """
    Virtual try-on endpoint using FLUX.2-klein-9B multi-reference editing
    
    Takes a person image and garment image, returns the person wearing the garment.
    """
    global pipe
    
    if pipe is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please wait for model initialization or check server logs."
        )
    
    try:
        # Decode input images
        person_img = decode_base64_image(request.person_image)
        garment_img = decode_base64_image(request.garment_image)
        
        # Resize images to target dimensions
        person_img = person_img.resize((request.width, request.height), Image.Resampling.LANCZOS)
        garment_img = garment_img.resize((request.width, request.height), Image.Resampling.LANCZOS)
        
        # Set seed for reproducibility
        seed = request.seed if request.seed is not None else torch.randint(0, 2**32, (1,)).item()
        generator = torch.Generator(device="cpu").manual_seed(seed)
        
        # Run inference with multi-reference input
        # The model takes a list of images for multi-reference editing
        result = pipe(
            prompt=request.prompt,
            image=[person_img, garment_img],
            height=request.height,
            width=request.width,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
            generator=generator,
        )
        
        result_image = result.images[0]
        
        # Encode result to base64
        result_base64 = encode_image_to_base64(result_image)
        
        return TryOnResponse(
            result_image=f"data:image/png;base64,{result_base64}",
            seed_used=seed
        )
        
    except Exception as e:
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
    global pipe
    
    if pipe is None:
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
        
        # Resize images
        person_img = person_img.resize((width, height), Image.Resampling.LANCZOS)
        garment_img = garment_img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Set seed
        actual_seed = seed if seed is not None else torch.randint(0, 2**32, (1,)).item()
        generator = torch.Generator(device="cpu").manual_seed(actual_seed)
        
        # Run inference
        result = pipe(
            prompt=prompt,
            image=[person_img, garment_img],
            height=height,
            width=width,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        )
        
        result_image = result.images[0]
        
        # Return as streaming response (PNG)
        buffer = io.BytesIO()
        result_image.save(buffer, format="PNG")
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="image/png",
            headers={
                "X-Seed-Used": str(actual_seed),
                "Content-Disposition": f"attachment; filename=tryon_result_{actual_seed}.png"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "FLUX.2 Klein Virtual Try-On POC",
        "version": "0.1.0",
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
