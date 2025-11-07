# Text Encoder Microservice

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
- Download CLIP and VAE models

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Test Standalone Mode
```bash
python main.py --mode standalone \
  --image1_path input/masked_person.png \
  --image2_path input/cloth.png \
  --prompt "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."

# To get tensor output without saving:
python main.py --mode standalone \
  --image1_path input/masked_person.png \
  --image2_path input/cloth.png \
  --prompt "your prompt here" \
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
- `image1_path`: Path to first image (masked person - needs scaling)
- `image2_path`: Path to second image (cloth image)
- `prompt`: Text prompt for positive conditioning
- `negative_prompt`: Text prompt for negative conditioning (optional, default: "")

### Outputs
- `positive_encoding_tensor`: Positive conditioning tensor
- `negative_encoding_tensor`: Negative conditioning tensor
- `positive_encoding_shape`: Shape of positive encoding
- `negative_encoding_shape`: Shape of negative encoding

See `API.md` for complete API documentation.

## Models Required

- **CLIP Model**: `qwen_2.5_vl_7b_fp8_scaled.safetensors` (in `models/clip/`)
- **VAE Model**: `qwen_image_vae.safetensors` (in `models/vae/`)

Both models are automatically downloaded by `setup.sh`.

## Environment Variables

Copy `.env.example` to `.env` and customize as needed:
```bash
cp .env.example .env
```



