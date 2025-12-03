# Qwen GPU Server

Production-ready GPU inference microservice for Qwen Image Edit virtual try-on.

## Features

- ✅ Async inference processing (202 Accepted immediately)
- ✅ GPU busy state management (429 when busy)
- ✅ Internal authentication (X-Internal-Auth header)
- ✅ Asset Service callbacks (never returns images in HTTP)
- ✅ Structured JSON logging
- ✅ Health, version, and metrics endpoints
- ✅ Self-contained (all dependencies included)

## Structure

```
gpu-server-qwen/
├── app/
│   ├── main.py              # FastAPI application
│   ├── routers/            # API endpoints
│   │   ├── tryon.py        # POST /tryon
│   │   ├── gpu_status.py  # GET /gpu/status
│   │   ├── health.py       # GET /health
│   │   ├── version.py      # GET /version
│   │   └── metrics.py      # GET /metrics
│   └── service/            # Business logic
│       ├── config.py       # Configuration management
│       ├── auth.py         # Authentication middleware
│       ├── scheduler.py    # GPU state management
│       ├── inference.py    # Inference execution
│       ├── asset_callback.py  # Asset Service callbacks
│       ├── logger.py       # JSON logging
│       └── utils_image.py  # Image utilities
├── configs/
│   └── config.yaml         # Server configuration
├── models/
│   └── request_models.py   # Pydantic models
├── comfy/                  # ComfyUI core
├── custom_nodes/           # Custom nodes
└── model_cache.py          # Model caching

```

## Configuration

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

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download models (if needed):
```bash
./download.sh
```

3. Configure `configs/config.yaml` with your settings

4. Run the server:
```bash
python run_server.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t qwen-gpu-server .
docker run --gpus all -p 8000:8000 -v $(pwd)/models:/app/models qwen-gpu-server
```

## API Endpoints

### POST /tryon
Virtual try-on inference endpoint.

**Headers:**
- `X-Internal-Auth: <BRIDGE_TO_GPU_SECRET>`

**Form Data:**
- `job_id` (str): Unique job identifier
- `user_id` (str): User identifier
- `session_id` (str): Session identifier
- `provider` (str): Always "qwen"
- `masked_user_image` (file): Masked user image
- `garment_image` (file): Garment image
- `config` (str, optional): JSON string with inference settings

**Response:**
- `202 Accepted`: Job accepted, processing asynchronously
- `429 Too Many Requests`: GPU is busy
- `401 Unauthorized`: Invalid auth token

### GET /gpu/status
Get GPU status for CPU Bridge scheduler.

**Response:**
```json
{
  "node_id": "qwen-gpu-1",
  "busy": false,
  "current_job_id": null,
  "queue_length": 0
}
```

### GET /health
Health check endpoint.

### GET /version
Version information.

### GET /metrics
Prometheus-style metrics.

## Development

All dependencies are included in this folder. The application does not depend on files outside this directory.

