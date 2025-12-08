# Qwen GPU Server

Production-ready GPU inference microservice for Qwen Image Edit virtual try-on.

## How It Works

The Qwen GPU Server is a FastAPI-based microservice that processes virtual try-on inference requests asynchronously:

1. **Request Flow**: CPU Bridge (via Load Balancer) sends job requests to `/tryon` endpoint
2. **Immediate Response**: Server returns `202 Accepted` immediately if GPU is available
3. **Async Processing**: Inference runs in background task, never blocks HTTP response
4. **Callback Delivery**: Results are sent to Asset Service via HTTP POST callback
5. **State Management**: Thread-safe scheduler tracks GPU busy state and job queue

**Key Features:**
- ✅ Async inference (202 Accepted immediately)
- ✅ GPU busy state management (429 when busy)
- ✅ Internal authentication (X-Internal-Auth header)
- ✅ Asset Service callbacks (never returns images in HTTP)
- ✅ Structured JSON logging
- ✅ Health, version, and metrics endpoints
- ✅ Self-contained (all dependencies included)

## Setup

### Prerequisites
- Python 3.8+
- CUDA-capable GPU
- PyTorch with CUDA support

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Download models (if needed):**
```bash
./download.sh
```

3. **Configure server:**
Edit `configs/config.yaml`:
```yaml
server:
  node_id: "qwen-gpu-1"

security:
  internal_auth_token: "BRIDGE_TO_GPU_SECRET"

asset_service:
  callback_url: "https://asset-service.internal/v1/vton/result"
  internal_auth_token: "GPU_TO_ASSET_SECRET"
  timeout: 10
  retries: 3

model:
  model_type: "qwen"
  model_version: "1.0.0"
  device: "cuda"
```

4. **Run the server:**
```bash
python run_server.py
```

**Note:** Do not use `uvicorn` directly from the command line, as it may conflict with ComfyUI's main.py. Always use `python run_server.py` instead.

If you need to use uvicorn directly, use the Python module syntax:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t qwen-gpu-server .
docker run --gpus all -p 8000:8000 -v $(pwd)/models:/app/models qwen-gpu-server
```

## Code Structure

```
gpu-server-qwen/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── routers/                # API endpoint handlers
│   │   ├── tryon.py           # POST /tryon - Virtual try-on endpoint
│   │   ├── gpu_status.py      # GET /gpu/status - GPU state for scheduler
│   │   ├── health.py          # GET /health - Health check
│   │   ├── version.py        # GET /version - Version info
│   │   └── metrics.py         # GET /metrics - Prometheus metrics
│   └── service/               # Business logic services
│       ├── config.py          # Configuration management (YAML loader)
│       ├── auth.py            # Internal authentication middleware
│       ├── scheduler.py      # Thread-safe GPU state scheduler
│       ├── inference.py      # ComfyUI inference execution
│       ├── asset_callback.py # Asset Service HTTP callback sender
│       ├── logger.py         # Structured JSON logging
│       └── utils_image.py    # Image validation and file utilities
├── configs/
│   ├── config.yaml           # Server configuration (required)
│   └── config.yaml.example   # Configuration template
├── models/
│   └── request_models.py     # Pydantic request/response models
├── comfy/                    # ComfyUI core library
├── comfy_api/                # ComfyUI API bindings
├── comfy_execution/          # ComfyUI execution engine
├── comfy_extras/             # ComfyUI extra nodes
├── custom_nodes/             # Custom ComfyUI nodes
├── model_cache.py            # Model loading and caching
├── run_server.py             # Server startup script
└── requirements.txt          # Python dependencies
```

## Folder Structure

### Core Application (`app/`)
- **`main.py`**: FastAPI app initialization, lifespan management, middleware setup
- **`routers/`**: REST API endpoint definitions
- **`service/`**: Core business logic and utilities

### Configuration (`configs/`)
- **`config.yaml`**: Runtime configuration (node ID, auth tokens, callback URLs)
- **`config.yaml.example`**: Template for new deployments

### Models (`models/`)
- **`request_models.py`**: Pydantic models for request/response validation

### ComfyUI Integration
- **`comfy/`**: Core ComfyUI library (diffusion models, samplers, etc.)
- **`comfy_api/`**: Python API bindings for ComfyUI
- **`comfy_execution/`**: Workflow execution engine
- **`comfy_extras/`**: Additional ComfyUI nodes
- **`custom_nodes/`**: Custom nodes for virtual try-on

### Utilities
- **`model_cache.py`**: Model loading, caching, and memory management
- **`run_server.py`**: Server startup and configuration loader

## API Endpoints

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for detailed endpoint documentation.

### Quick Reference
- `POST /tryon` - Virtual try-on inference (requires auth)
- `GET /gpu/status` - GPU state for scheduler (requires auth)
- `GET /health` - Health check (public)
- `GET /version` - Version information (public)
- `GET /metrics` - Prometheus metrics (public)

## Development

All dependencies are included in this folder. The application does not depend on files outside this directory.
