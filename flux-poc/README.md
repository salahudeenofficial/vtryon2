# FLUX.2 [klein] 9B Virtual Try-On POC

A proof-of-concept virtual try-on application using Black Forest Labs' FLUX.2-klein-9B model with native multi-reference editing capabilities.

## Features

- **Multi-Reference Input**: No image stitching required - upload person and garment images separately
- **Fast Inference**: Distilled to 4 steps for sub-second generation
- **Simple Web UI**: Configure server IP, upload images, and test the model
- **REST API**: FastAPI server with OpenAPI documentation

## Requirements

- Python 3.10+
- CUDA-capable GPU with ~29GB VRAM (RTX 4090 or better recommended)
- HuggingFace account with access to FLUX.2-klein-9B model

## Quick Start (Vast.ai / Remote Server)

### 1. Setup Environment

```bash
# Clone the repo (if not already done)
git clone <your-repo-url>
cd vtryon2/flux-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Login to HuggingFace

You need to accept the model license and login:

```bash
# Login to HuggingFace (you'll need a token)
huggingface-cli login
```

Visit https://huggingface.co/black-forest-labs/FLUX.2-klein-9B and accept the license agreement.

### 3. Start the Server

```bash
# Run the server
python server.py

# Or with uvicorn for more options
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server will:
1. Load the FLUX.2-klein-9B model (~29GB VRAM)
2. Start listening on port 8000

### 4. Access the Web UI

Open `index.html` in your browser (can be opened locally, it connects to the remote server).

1. Enter your server URL (e.g., `http://<vast-ai-ip>:8000`)
2. Click "Test Connection" to verify
3. Upload a person image and a garment image
4. Click "Generate Try-On"

## API Endpoints

### Health Check
```bash
GET /health
```
Returns server status, GPU info, and model loading state.

### Virtual Try-On (Base64)
```bash
POST /tryon
Content-Type: application/json

{
    "person_image": "<base64-encoded-image>",
    "garment_image": "<base64-encoded-image>",
    "prompt": "A photo of the person wearing the garment...",
    "num_inference_steps": 4,
    "guidance_scale": 1.0,
    "width": 1024,
    "height": 1024,
    "seed": null
}
```

### Virtual Try-On (File Upload)
```bash
POST /tryon/upload
Content-Type: multipart/form-data

- person_image: <file>
- garment_image: <file>
- prompt: <string>
- num_inference_steps: <int>
- guidance_scale: <float>
- width: <int>
- height: <int>
- seed: <int|null>
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt` | "A photo of the person wearing the garment..." | Text prompt for generation |
| `num_inference_steps` | 4 | Number of denoising steps (4 is optimal for klein) |
| `guidance_scale` | 1.0 | Classifier-free guidance scale |
| `width` | 1024 | Output image width |
| `height` | 1024 | Output image height |
| `seed` | Random | Seed for reproducibility |

## Vast.ai Setup Tips

1. **Instance Selection**: Choose an instance with RTX 4090 or A100 (40GB+)
2. **Port Forwarding**: Make sure port 8000 is exposed
3. **Disk Space**: Model requires ~20GB download space

### Example Vast.ai Command
```bash
# After SSH into your instance
cd /workspace
git clone <your-repo>
cd vtryon2/flux-poc

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Login to HF
huggingface-cli login

# Run server (in background)
nohup python server.py > server.log 2>&1 &

# Check logs
tail -f server.log
```

## Model Information

- **Model**: [FLUX.2-klein-9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B)
- **Parameters**: 9 Billion
- **Text Encoder**: 8B Qwen3
- **License**: Non-commercial
- **Inference Steps**: Optimized for 4 steps

## Troubleshooting

### Out of Memory
- Use `pipe.enable_model_cpu_offload()` (enabled by default)
- Reduce image dimensions (512x512 instead of 1024x1024)
- Use FP8 quantized version if available

### Model Not Loading
- Ensure you've accepted the license on HuggingFace
- Check `huggingface-cli whoami` to verify login
- Check disk space for model download

### Connection Issues
- Verify port 8000 is exposed on your instance
- Check firewall settings
- Try using the instance's public IP

## License

This POC uses the FLUX.2-klein-9B model which is under the [FLUX Non-Commercial License](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B).
