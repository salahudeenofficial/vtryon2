# Sampling Microservice

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
- Download UNET and LoRA models

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Test Standalone Mode
```bash
python main.py --mode standalone \
  --positive_encoding test_outputs/text_encoder_positive_output.pt \
  --negative_encoding test_outputs/text_encoder_negative_output.pt \
  --latent_image test_outputs/latent_encoder_output.pt \
  --seed 12345

# To get tensor output without saving:
python main.py --mode standalone \
  --positive_encoding test_outputs/text_encoder_positive_output.pt \
  --negative_encoding test_outputs/text_encoder_negative_output.pt \
  --latent_image test_outputs/latent_encoder_output.pt \
  --seed 12345 \
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
- `positive_encoding`: Path to positive encoding .pt file (from text_encoder)
- `negative_encoding`: Path to negative encoding .pt file (from text_encoder)
- `latent_image`: Path to latent image .pt file (from latent_encoder)
- `seed`: Random seed (optional, random if not provided)
- `steps`: Number of sampling steps (default: 4)
- `cfg`: CFG scale (default: 1.0)
- `sampler_name`: Sampler name (default: "euler")
- `scheduler`: Scheduler name (default: "simple")
- `denoise`: Denoise strength (default: 1.0)

### Outputs
- `sampled_latent_tensor`: Sampled latent tensor
- `sampled_latent_shape`: Shape of sampled latent
- `sampled_latent_dict`: Dict format `{"samples": tensor}` for decoder compatibility

See `API.md` for complete API documentation.

## Models Required

- **UNET Model**: `qwen_image_edit_2509_fp8_e4m3fn.safetensors` (in `models/diffusion_models/`)
- **LoRA Model**: `Qwen-Image-Lightning-4steps-V2.0.safetensors` (in `models/loras/`)

Both models are automatically downloaded by `setup.sh`.

## Environment Variables

Copy `.env.example` to `.env` and customize as needed:
```bash
cp .env.example .env
```

## Processing Pipeline

1. Load UNET model
2. Load LoRA model and apply to UNET
3. Apply ModelSamplingAuraFlow transformation (shift parameter)
4. Apply CFGNorm transformation (strength parameter)
5. Run KSampler with all inputs
6. Return sampled latent tensor



