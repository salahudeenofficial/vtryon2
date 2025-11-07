# Text Encoder Microservice - Implementation Plan

## Overview
The text encoder microservice encodes text prompts and images into conditioning tensors for diffusion sampling. It uses the `TextEncodeQwenImageEditPlus` node which requires CLIP, VAE, and two images.

## Implementation Steps

### Step 1: Create Core Service Files
Based on `latent_encoder` structure, create:

1. **`config.py`** - Configuration management
   - Load environment variables
   - Define model paths (CLIP, VAE)
   - Define output directory
   - Default values for models and parameters

2. **`errors.py`** - Custom exceptions
   - `ImageNotFoundError`
   - `CLIPModelNotFoundError`
   - `VAEModelNotFoundError`
   - `EncodingFailedError`
   - `OutputDirNotWritableError`
   - `ScalingFailedError`
   - `ComfyUIInitializationError`

3. **`models.py`** - Pydantic data models
   - `TextEncoderRequest` (for standalone mode)
   - `TextEncoderResponse`
   - `KafkaTextEncoderRequest` (for Kafka mode)
   - `KafkaTextEncoderResponse`

4. **`utils.py`** - Utility functions
   - Copy from `latent_encoder/utils.py` (same utilities needed)
   - `get_value_at_index`
   - `add_comfyui_directory_to_sys_path`
   - `add_extra_model_paths`
   - `generate_request_id`
   - `ensure_directory_exists`

5. **`service.py`** - Core encoding logic
   - `setup_comfyui()` - Initialize ComfyUI paths and models
   - `encode_text_and_images()` - Main encoding function
     - Load CLIP model
     - Load VAE model
     - Load and scale image1 (masked person)
     - Load image2 (cloth)
     - Encode positive prompt
     - Encode negative prompt
     - Extract tensors from outputs
     - Return both conditioning tensors

6. **`kafka_handler.py`** - Kafka consumer/producer
   - Consumer for text encoder requests
   - Producer for text encoder responses
   - Message serialization/deserialization

7. **`main.py`** - Entry point
   - CLI argument parsing
   - Mode selection (standalone/kafka)
   - Service initialization

### Step 2: Create Setup Scripts

1. **`setup.sh`** - Comprehensive setup script
   - Create Python 3.13 virtual environment
   - Install PyTorch with CUDA 13.0
   - Clone ComfyUI files from master branch
   - Clone requirements.txt and append additional dependencies
   - Install all dependencies
   - Download required models (CLIP and VAE)

2. **`.env.example`** - Environment variable template
   - Kafka configuration
   - Model paths
   - Output directory

### Step 3: Update Documentation

1. **`README.md`** - Quick start guide
   - Setup instructions
   - Usage examples (standalone and Kafka)
   - Testing instructions

2. **`API.md`** - Update with implementation details
   - Input/output specifications
   - Error handling
   - Examples

### Step 4: Key Implementation Details

#### Service Function Signature
```python
def encode_text_and_images(
    image1_path: str,  # Masked person image (needs scaling)
    image2_path: str,  # Cloth image
    prompt: str,  # Positive prompt
    negative_prompt: str = "",  # Negative prompt (default empty)
    clip_model_name: str = None,  # Default from config
    vae_model_name: str = None,  # Default from config
    upscale_method: str = "lanczos",
    megapixels: float = 1.0,
    output_dir: str = None,
    request_id: str = None,
    save_tensor: bool = True
) -> dict
```

#### ComfyUI Nodes Required
1. **CLIPLoader** - Load CLIP model
2. **VAELoader** - Load VAE model
3. **LoadImage** - Load both images
4. **ImageScaleToTotalPixels** - Scale image1
5. **TextEncodeQwenImageEditPlus** - Encode prompts with images

#### Output Format
- Returns dict with:
  - `positive_encoding_tensor`: torch.Tensor (or path if saved)
  - `negative_encoding_tensor`: torch.Tensor (or path if saved)
  - `positive_encoding_shape`: tuple
  - `negative_encoding_shape`: tuple
  - `metadata`: dict with processing info

#### Tensor Extraction
Text encoder outputs are typically in format: `[tensor, metadata_dict]`
- Extract first element (tensor) for saving/comparison
- Preserve original format for passing to sampler

### Step 5: Model Dependencies

#### Required Models
1. **CLIP Model**: `qwen_2.5_vl_7b_fp8_scaled.safetensors`
   - Location: `models/clip/`
   - Download in `setup.sh`

2. **VAE Model**: `qwen_image_vae.safetensors`
   - Location: `models/vae/`
   - Download in `setup.sh`

### Step 6: Testing

1. **Standalone Test**
   ```bash
   python main.py --mode standalone \
     --image1 input/masked_person.png \
     --image2 input/cloth.png \
     --prompt "your prompt here"
   ```

2. **Tensor Comparison Test**
   - Create `test_step2.py` in parent directory
   - Compare `text_encoder_positive_output.pt` and `text_encoder_negative_output.pt`
   - From `workflow_script_serial_test.py` with actual service output

### Step 7: File Structure
```
text_encoder/
├── config.py
├── errors.py
├── models.py
├── utils.py
├── service.py
├── kafka_handler.py
├── main.py
├── setup.sh
├── .env.example
├── README.md
├── API.md
├── Dockerfile
├── requirements.txt
├── comfyui/          # Cloned from master branch
├── models/           # Downloaded models
│   ├── clip/
│   └── vae/
└── venv/             # Virtual environment
```

## Implementation Order

1. ✅ Copy `utils.py` from `latent_encoder` (same utilities)
2. ✅ Create `config.py` (similar to `latent_encoder`, add CLIP model path)
3. ✅ Create `errors.py` (add CLIPModelNotFoundError)
4. ✅ Create `models.py` (TextEncoderRequest/Response)
5. ✅ Create `service.py` (main encoding logic)
6. ✅ Create `kafka_handler.py` (Kafka integration)
7. ✅ Create `main.py` (entry point)
8. ✅ Create `setup.sh` (setup script with CLIP+VAE download)
9. ✅ Create `.env.example`
10. ✅ Update `README.md`
11. ✅ Test standalone mode
12. ✅ Create `test_step2.py` for tensor comparison

## Key Differences from Latent Encoder

1. **Two Images**: Requires both image1 (scaled) and image2 (not scaled)
2. **CLIP Model**: Needs CLIPLoader in addition to VAELoader
3. **Two Outputs**: Returns both positive and negative conditioning tensors
4. **TextEncodeQwenImageEditPlus**: Uses custom node instead of standard VAEEncode
5. **Conditioning Format**: Outputs are in conditioning format `[tensor, metadata_dict]`

## Next Steps

1. Start with Step 1: Create core service files
2. Test with standalone mode
3. Verify tensor extraction matches `workflow_script_serial_test.py` output
4. Implement Kafka handler
5. Create test comparison script



