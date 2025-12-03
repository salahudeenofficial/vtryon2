# Integration Guide

Concise documentation for integrating with Qwen GPU Server.

## Authentication

All endpoints (except `/health`, `/version`, `/metrics`) require the `X-Internal-Auth` header:

```
X-Internal-Auth: <BRIDGE_TO_GPU_SECRET>
```

Configure the secret in `configs/config.yaml` under `security.internal_auth_token`.

## Endpoints

### POST /tryon

Virtual try-on inference endpoint. Accepts job and returns 202 immediately. Processes asynchronously and sends results via callback.

**Request from CPU Bridge (via Load Balancer):**

**Headers:**
```
X-Internal-Auth: <BRIDGE_TO_GPU_SECRET>
Content-Type: multipart/form-data
```

**Form Data:**
- `job_id` (string, required): Unique job identifier
- `user_id` (string, required): User identifier
- `session_id` (string, required): Session identifier
- `provider` (string, required): Must be `"qwen"`
- `masked_user_image` (file, required): Masked user image (PNG/JPEG)
- `garment_image` (file, required): Garment image (PNG/JPEG)
- `config` (string, optional): JSON string with inference parameters:
  ```json
  {
    "prompt": "custom prompt text",
    "seed": 12345,
    "steps": 4,
    "cfg": 1.0
  }
  ```

**Response:**
- `202 Accepted`: Job accepted, processing asynchronously
  ```json
  {
    "job_id": "job-123",
    "status": "ACCEPTED",
    "node_id": "qwen-gpu-1"
  }
  ```
- `429 Too Many Requests`: GPU is busy
  ```json
  {
    "job_id": "job-123",
    "status": "REJECTED_BUSY",
    "node_id": "qwen-gpu-1",
    "message": "GPU is busy. Try another node."
  }
  ```
- `401 Unauthorized`: Invalid auth token
- `400 Bad Request`: Invalid provider or missing fields

**Result Delivery (Callback to Asset Service):**

The server sends results to the callback URL configured in `configs/config.yaml` (`asset_service.callback_url`).

**Callback Request Format:**

**Method:** `POST`

**Headers:**
```
X-Internal-Auth: <GPU_TO_ASSET_SECRET>
Content-Type: multipart/form-data
```

**Form Data:**
- `job_id` (string): Original job identifier
- `user_id` (string): User identifier
- `session_id` (string): Session identifier
- `provider` (string): Always `"qwen"`
- `node_id` (string): GPU node identifier
- `model_version` (string): Model version used
- `inference_time_ms` (string): Inference duration in milliseconds
- `output_image` (file): Result image (PNG format)
- `error` (string, optional): Error message if inference failed

**Success Response:**
- `200 OK`: Callback received successfully

**Error Handling:**
- Server retries callback up to 3 times (configurable) with exponential backoff
- If all retries fail, error is logged but job is still marked complete

### GET /gpu/status

Get GPU status for CPU Bridge scheduler. Used by load balancer to route jobs.

**Request:**

**Headers:**
```
X-Internal-Auth: <BRIDGE_TO_GPU_SECRET>
```

**Response:**
```json
{
  "node_id": "qwen-gpu-1",
  "busy": false,
  "current_job_id": null,
  "queue_length": 0
}
```

**Fields:**
- `node_id`: GPU node identifier
- `busy`: Whether GPU is currently processing a job
- `current_job_id`: ID of job being processed (null if idle)
- `queue_length`: Number of jobs in queue

### GET /health

Health check endpoint. No authentication required.

**Response:**
```json
{
  "status": "ok",
  "gpu_available": true,
  "model_loaded": true,
  "node_id": "qwen-gpu-1"
}
```

**Fields:**
- `status`: Always `"ok"` if server is running
- `gpu_available`: Whether CUDA GPU is available
- `model_loaded`: Whether models are loaded into memory
- `node_id`: GPU node identifier

### GET /version

Version information. No authentication required.

**Response:**
```json
{
  "model_type": "qwen",
  "model_version": "1.0.0",
  "backend": "comfyui-python",
  "git_commit": "abc1234",
  "node_id": "qwen-gpu-1"
}
```

### GET /metrics

Prometheus-style metrics. No authentication required.

**Response:**
```json
{
  "vton_inference_count": 150,
  "vton_inference_latency_ms": 2500.5,
  "vton_inference_errors_total": 2,
  "gpu_memory_used_bytes": 8589934592,
  "gpu_utilization_percent": 85.5
}
```

## Request Flow

1. **CPU Bridge** (via Load Balancer) → `POST /tryon` with job data
2. **GPU Server** → Returns `202 Accepted` immediately
3. **GPU Server** → Processes inference asynchronously
4. **GPU Server** → `POST` to Asset Service callback URL with results
5. **Asset Service** → Returns `200 OK` to acknowledge receipt

## Error Scenarios

### GPU Busy (429)
- Server returns `429 Too Many Requests` with `Retry-After` header
- CPU Bridge should route to another node

### Inference Failure
- Server sends callback with `error` field populated
- Job is marked complete, GPU freed

### Callback Failure
- Server retries up to 3 times with exponential backoff
- If all retries fail, error is logged
- Job is still marked complete

## Configuration

All configuration is in `configs/config.yaml`:

- `server.node_id`: Unique identifier for this GPU node
- `security.internal_auth_token`: Secret for CPU Bridge requests
- `asset_service.callback_url`: URL to send inference results
- `asset_service.internal_auth_token`: Secret for Asset Service callbacks
- `asset_service.timeout`: Callback timeout in seconds (default: 10)
- `asset_service.retries`: Number of callback retries (default: 3)
- `model.model_type`: Model type identifier
- `model.model_version`: Model version string
- `model.device`: Device to use (`cuda` or `cpu`)

