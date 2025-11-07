# Decoding Microservice

## Quick Start

### 1. Setup (Clone modules and download models)
```bash
bash setup.sh
```

This will:
- Create Python 3.13 virtual environment
- Install PyTorch with CUDA 13.0
- Clone ComfyUI modules from master branch
- Install all dependencies
- Download VAE model

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Test Standalone Mode
```bash
python main.py --mode standalone \
  --latent test_outputs/sampling_output.pt \
  --output_filename test_output \
  --output_format jpg

# To get tensor output without saving:
python main.py --mode standalone \
  --latent test_outputs/sampling_output.pt \
  --output_filename test_output \
  --output_format jpg \
  --no-save
```

### 4. Test Kafka Mode
```bash
python main.py --mode kafka
```

## Service Modes

- **standalone**: Direct execution for testing
- **kafka**: Kafka consumer/producer

## Input/Output

### Inputs
- `latent`: Path to latent .pt file (from sampling microservice)
- `vae_model_name`: VAE model name (default: "qwen_image_vae.safetensors")
- `output_filename`: Base name for output image file (default: "output")
- `output_format`: Image format - "jpg", "png", or "webp" (default: "jpg")

### Outputs
- `image_file_path`: Path to saved image file
- `image_shape`: Shape of decoded image (height, width, channels)
- `image_tensor`: Image tensor (for testing/comparison)
- `file_size`: Size of output file in bytes

See `API.md` for complete API documentation.

## Models Required

- **VAE Model**: `qwen_image_vae.safetensors` (in `models/vae/`)

The model is automatically downloaded by `setup.sh`.

## Environment Variables

Copy `.env.example` to `.env` and customize as needed:
```bash
cp .env.example .env
```

## Processing Pipeline

1. Load VAE model
2. Load latent tensor from file (or accept tensor directly)
3. Prepare latent in dict format `{"samples": tensor}`
4. Run VAEDecode to convert latent to image tensor
5. Normalize and convert image tensor to [0, 255] uint8
6. Save image using PIL/Pillow

## Supported Image Formats

- **JPEG** (jpg/jpeg): Best for photos, smaller file size
- **PNG**: Lossless, supports transparency
- **WebP**: Modern format, good compression



