# Decoding Microservice - Implementation Plan

## Overview
The decoding microservice decodes latent tensors back to image files using VAE decoder. It's the final step in the pipeline, converting sampled latents to actual images.

## Implementation Steps

### Step 1: Create Core Service Files
Based on previous microservices structure, create:

1. **`config.py`** - Configuration management
   - Load environment variables
   - Define VAE model path
   - Define output directory and format defaults

2. **`errors.py`** - Custom exceptions
   - `VAEModelNotFoundError`
   - `LatentFileNotFoundError`
   - `DecodingFailedError`
   - `OutputDirNotWritableError`
   - `InvalidImageFormatError`
   - `ComfyUIInitializationError`

3. **`models.py`** - Pydantic data models
   - `DecodingRequest` (for standalone mode)
   - `DecodingResponse`
   - `KafkaDecodingRequest` (for Kafka mode)
   - `KafkaDecodingResponse`

4. **`utils.py`** - Utility functions
   - Copy from `latent_encoder/utils.py` (same utilities needed)
   - `get_value_at_index`
   - `add_comfyui_directory_to_sys_path`
   - `add_extra_model_paths`
   - `generate_request_id`
   - `ensure_directory_exists`
   - `load_tensor_from_file` (from sampling/utils.py)

5. **`service.py`** - Core decoding logic
   - `setup_comfyui()` - Initialize ComfyUI paths and models
   - `decode_latent_to_image()` - Main decoding function
     - Load VAE model
     - Load latent tensor from file or accept tensor directly
     - Prepare latent in dict format `{"samples": tensor}`
     - Run VAEDecode
     - Extract image tensor
     - Save image using PIL/Pillow
     - Return image file path and metadata

6. **`kafka_handler.py`** - Kafka consumer/producer
   - Consumer for decoding requests
   - Producer for decoding responses
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
   - Download required models (VAE only)

2. **`.env.example`** - Environment variable template
   - Kafka configuration
   - Model paths
   - Output directory
   - Default image format

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
def decode_latent_to_image(
    latent: Union[str, torch.Tensor, dict],  # Path to .pt file, tensor, or dict format
    vae_model_name: str = None,  # Default from config
    output_filename: str = "output",
    output_dir: str = None,
    output_format: str = "jpg",  # jpg, png, webp
    request_id: str = None,
    save_image: bool = True
) -> dict
```

#### ComfyUI Nodes Required
1. **VAELoader** - Load VAE model
2. **VAEDecode** - Decode latent to image

#### Input Format Handling
- Accept `.pt` file paths OR tensor objects OR dict format directly
- Latent must be in dict format `{"samples": tensor}` for VAEDecode
- Handle wrapping if needed

#### Output Format
- Returns dict with:
  - `image_file_path`: str (path to saved image)
  - `image_shape`: tuple (height, width, channels)
  - `image_tensor`: torch.Tensor (if not saved)
  - `file_size`: int (bytes)
  - `metadata`: dict

#### Image Saving
- Use PIL/Pillow to save images
- Support formats: jpg, png, webp
- Handle image tensor format: `[batch, height, width, channels]` or `[height, width, channels]`
- Normalize values to [0, 255] uint8 range

### Step 5: Model Dependencies

#### Required Models
1. **VAE Model**: `qwen_image_vae.safetensors`
   - Location: `models/vae/`
   - Download in `setup.sh`

### Step 6: Image Format Handling

The decoder outputs image tensors in format:
- Shape: `[batch, height, width, channels]` or `[height, width, channels]`
- Values: Typically in range [0, 1] or [-1, 1]
- Need to:
  - Normalize to [0, 1] if needed
  - Convert to [0, 255] uint8
  - Handle batch dimension
  - Save using PIL

### Step 7: Testing

1. **Standalone Test**
   ```bash
   python main.py --mode standalone \
     --latent test_outputs/sampling_output.pt \
     --output_filename test_output \
     --output_format jpg
   ```

2. **Tensor Comparison Test**
   - Create `test_step4.py` in parent directory
   - Compare `decoding_output.pt` from `workflow_script_serial_test.py`
   - With actual service output (image tensor)

### Step 8: File Structure
```
decoding/
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
│   └── vae/
└── venv/             # Virtual environment
```

## Implementation Order

1. ✅ Copy `utils.py` from `latent_encoder` (add `load_tensor_from_file` from sampling)
2. ✅ Create `config.py` (add VAE model path, output format defaults)
3. ✅ Create `errors.py` (add decoding-specific errors)
4. ✅ Create `models.py` (DecodingRequest/Response)
5. ✅ Create `service.py` (main decoding logic)
6. ✅ Create `kafka_handler.py` (Kafka integration)
7. ✅ Create `main.py` (entry point)
8. ✅ Create `setup.sh` (setup script with VAE download)
9. ✅ Create `.env.example`
10. ✅ Update `README.md`
11. ✅ Test standalone mode
12. ✅ Create `test_step4.py` for tensor comparison

## Key Differences from Previous Microservices

1. **Image Output**: Saves actual image files (jpg/png/webp), not just tensors
2. **Single Model**: Only needs VAE model (simpler than sampling)
3. **Image Format Handling**: Needs to handle image tensor normalization and format conversion
4. **File I/O**: Saves image files using PIL/Pillow
5. **Output Format**: Returns image file path instead of tensor path

## Next Steps

1. Start with Step 1: Create core service files
2. Test with standalone mode using sampling output
3. Verify image output matches `workflow_script_serial_test.py` output
4. Implement Kafka handler
5. Create test comparison script



