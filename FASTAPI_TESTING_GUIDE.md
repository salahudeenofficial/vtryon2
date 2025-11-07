# FastAPI Route Explanation & Testing Guide

## Overview

The FastAPI server provides a virtual try-on service that:
1. Accepts a person image, mask type, and prompt
2. Creates a masked version of the person image
3. Runs the ComfyUI workflow to generate a virtual try-on result
4. Returns the generated image

## API Endpoints

### 1. POST `/tryon_extracted` - Main Virtual Try-On Endpoint

**Purpose**: Generate a virtual try-on image by placing a garment on a person.

**Request Format**: `multipart/form-data`

**Parameters**:
- `image` (file, required): Input person image file (PNG/JPEG)
- `mask_type` (string, required): Type of mask to apply
  - `upper_body`: Masks upper body clothing (shirts, tops)
  - `lower_body`: Masks lower body clothing (pants, skirts)
  - `other`: No masking (uses original image)
- `prompt` (string, required): Text prompt describing the desired result

**Response**: 
- Content-Type: `image/png`
- Body: Generated try-on image file

**Processing Flow**:
```
1. Upload image → Save to temp file
2. Call masked_image() → Create masked person image
3. Copy masked image to input/ directory as "masked_person.png"
4. Run workflow_script_serial.py:
   - Load models (UNET, CLIP, VAE, LoRA)
   - Encode masked person image to latent
   - Encode prompt with images
   - Run diffusion sampling
   - Decode latent to image
   - Save to output/ directory
5. Return generated image
6. Clean up temporary files
```

**Important Notes**:
- The `cloth.png` file must exist in the `input/` directory
- The workflow uses the cloth image from `input/cloth.png`
- Generated images are saved in `output/` directory

### 2. GET `/health` - Health Check

**Purpose**: Check if the server is running.

**Response**:
```json
{
  "status": "healthy"
}
```

## Testing Methods

### Method 1: Using curl (Command Line)

#### Basic Test
```bash
curl -X POST "http://localhost:8000/tryon_extracted" \
  -F "image=@person.jpg" \
  -F "mask_type=upper_body" \
  -F "prompt=by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1." \
  --output result.png
```

#### Test with Different Mask Types
```bash
# Upper body
curl -X POST "http://localhost:8000/tryon_extracted" \
  -F "image=@person.jpg" \
  -F "mask_type=upper_body" \
  -F "prompt=by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1." \
  --output result_upper.png

# Lower body
curl -X POST "http://localhost:8000/tryon_extracted" \
  -F "image=@person.jpg" \
  -F "mask_type=lower_body" \
  -F "prompt=by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1." \
  --output result_lower.png

# No masking
curl -X POST "http://localhost:8000/tryon_extracted" \
  -F "image=@person.jpg" \
  -F "mask_type=other" \
  -F "prompt=by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1." \
  --output result_other.png
```

#### Health Check
```bash
curl http://localhost:8000/health
```

### Method 2: Using Python requests

#### Basic Test Script
```python
import requests

# API endpoint
url = "http://localhost:8000/tryon_extracted"

# Prepare files and data
files = {
    "image": ("person.jpg", open("person.jpg", "rb"), "image/jpeg")
}
data = {
    "mask_type": "upper_body",
    "prompt": "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
}

# Send request
print("Sending request...")
response = requests.post(url, files=files, data=data)

# Check response
if response.status_code == 200:
    # Save the generated image
    with open("output.png", "wb") as f:
        f.write(response.content)
    print("✓ Success! Image saved to output.png")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
```

#### Advanced Test Script with Error Handling
```python
import requests
import sys
from pathlib import Path

def test_tryon(image_path: str, mask_type: str, prompt: str, output_path: str = "result.png"):
    """Test the tryon_extracted endpoint."""
    url = "http://localhost:8000/tryon_extracted"
    
    # Check if image exists
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return False
    
    # Prepare request
    with open(image_path, "rb") as f:
        files = {"image": (Path(image_path).name, f, "image/jpeg")}
        data = {
            "mask_type": mask_type,
            "prompt": prompt
        }
        
        try:
            print(f"📤 Sending request...")
            print(f"   Image: {image_path}")
            print(f"   Mask Type: {mask_type}")
            print(f"   Prompt: {prompt[:50]}...")
            
            response = requests.post(url, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                with open(output_path, "wb") as out:
                    out.write(response.content)
                print(f"✓ Success! Image saved to {output_path}")
                return True
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out (processing may take a while)")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

# Test different mask types
if __name__ == "__main__":
    image = "person.jpg"
    prompt = "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
    
    # Test upper body
    test_tryon(image, "upper_body", prompt, "result_upper.png")
    
    # Test lower body
    test_tryon(image, "lower_body", prompt, "result_lower.png")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"\nHealth check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
```

### Method 3: Using FastAPI Interactive Docs (Swagger UI)

1. Start the server:
   ```bash
   python api_server.py
   ```

2. Open browser and navigate to:
   ```
   http://localhost:8000/docs
   ```

3. Click on `POST /tryon_extracted` endpoint

4. Click "Try it out"

5. Fill in the form:
   - Upload an image file
   - Enter mask_type: `upper_body`, `lower_body`, or `other`
   - Enter prompt text

6. Click "Execute"

7. View the response (image will be shown or downloadable)

### Method 4: Using Postman

1. Create a new POST request to `http://localhost:8000/tryon_extracted`

2. Go to "Body" tab → Select "form-data"

3. Add three fields:
   - `image` (type: File) → Select your image file
   - `mask_type` (type: Text) → Enter: `upper_body`
   - `prompt` (type: Text) → Enter your prompt

4. Click "Send"

5. Save the response as an image file

## Prerequisites for Testing

### 1. Start the Server
```bash
# Option 1: Using setup.sh (recommended - sets up everything)
./setup.sh

# Option 2: Manual start
source venv/bin/activate
python api_server.py
```

### 2. Required Files
- `input/cloth.png` - The garment image to try on
- All models downloaded (via `download.sh`)
- StableVITON checkpoints (via `download_stableviton.sh`)

### 3. Test Image
- Prepare a person image (PNG or JPEG)
- Recommended size: 576x768 or similar portrait orientation

## Expected Response Times

- **Masking**: 5-15 seconds (depends on GPU)
- **Workflow Processing**: 30-60 seconds (depends on GPU and model loading)
- **Total**: 35-75 seconds per request

## Error Handling

### Common Errors

1. **400 Bad Request**
   - Invalid `mask_type` (must be `upper_body`, `lower_body`, or `other`)
   - Missing required parameters

2. **500 Internal Server Error**
   - `cloth.png` not found in `input/` directory
   - Model files not downloaded
   - GPU/CUDA issues
   - Processing errors

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

## Example Prompts

### Standard Prompt (Recommended)
```
by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.
```

### Custom Prompts
```
Place the shirt from the second image on the person, matching the green masked area position.
```

```
Apply the garment shown in image 2 to the person in image 1, using the green masked region as reference.
```

## Troubleshooting

### Server won't start
- Check if port 8000 is available
- Verify all dependencies are installed
- Check Python version (3.8+)

### Request fails with "cloth.png not found"
- Ensure `input/cloth.png` exists
- Check file permissions

### Request times out
- Processing takes time, increase timeout
- Check GPU availability
- Verify models are loaded correctly

### Image generation fails
- Check model files are downloaded
- Verify CUDA/GPU is available
- Check logs for specific errors

## Performance Tips

1. **First request is slow** - Models need to be loaded into memory
2. **Subsequent requests are faster** - Models stay in memory
3. **Use GPU** - Significantly faster than CPU
4. **Batch processing** - Consider implementing batch endpoint for multiple images

## Security Notes

- CORS is currently set to `allow_origins=["*"]` - restrict in production
- No authentication implemented - add authentication for production
- File uploads are not validated - add file type/size validation
- Temporary files are cleaned up, but consider adding cleanup on server restart

