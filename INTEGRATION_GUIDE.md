# CPU Bridge Integration Guide

This guide provides complete details for integrating with CPU Bridge, including all API endpoints, message queue formats, and Load Balancer integration.

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Load Balancer Integration](#load-balancer-integration)
3. [Configuration](#configuration)
4. [Error Handling](#error-handling)

---

## API Endpoints

### Base URL

```
http://cpu-bridge-host:8080
```

### Authentication

All endpoints (except `/health` and `/metrics`) require the `X-Internal-Auth` header:

```
X-Internal-Auth: <GATEWAY_TO_BRIDGE_SECRET>
```

Configure the secret in `configs/config.yaml`:
```yaml
auth:
  gateway_to_bridge_secret: "${GATEWAY_TO_BRIDGE_SECRET:-your-secret}"
```

---

### 1. POST /bridge/tryon

**Description**: Create a new VTON job and enqueue it for processing.

**Method**: `POST`

**Path**: `/bridge/tryon`

**Headers**:
```
X-Internal-Auth: <GATEWAY_TO_BRIDGE_SECRET>
Content-Type: application/json
```

**Request Body** (Flux Provider):
```json
{
  "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd",
  "user_id": "user-123",
  "session_id": "session-456",
  "provider": "flux",
  "storage_keys": {
    "user_image": "fashionx-storage/vton-inputs-private/28/48d15146-2a76-4b42-b2df-7f4f3f6292b7/b1ab0edc-0e6b-4b75-9930-1ee3031f1870/user.png",
    "user_mask": "fashionx-storage/vton-inputs-private/28/48d15146-2a76-4b42-b2df-7f4f3f6292b7/b1ab0edc-0e6b-4b75-9930-1ee3031f1870/mask.png",
    "garment_image": "fashionx-storage/vton-inputs-private/28/48d15146-2a76-4b42-b2df-7f4f3f6292b7/b1ab0edc-0e6b-4b75-9930-1ee3031f1870/garment.png"
  },
  "config": {
    "seed": 42,
    "steps": 30,
    "guidance_scale": 5.0
  }
}
```

**Request Body** (Qwen Provider):
```json
{
  "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd",
  "user_id": "user-123",
  "session_id": "session-456",
  "provider": "qwen",
  "storage_keys": {
    "masked_user_image": "fashionx-storage/vton-inputs-private/28/48d15146-2a76-4b42-b2df-7f4f3f6292b7/b1ab0edc-0e6b-4b75-9930-1ee3031f1870/masked_user.png",
    "garment_image": "fashionx-storage/vton-inputs-private/28/48d15146-2a76-4b42-b2df-7f4f3f6292b7/b1ab0edc-0e6b-4b75-9930-1ee3031f1870/garment.png"
  },
  "config": {
    "seed": 42,
    "steps": 30
  }
}
```

**Request Fields**:
- `job_id` (string, required): Job identifier provided by backend (UUID format)
- `user_id` (string, required): User identifier
- `session_id` (string, required): Session identifier (UUID format)
- `provider` (string, required): Provider type - `"flux"` or `"qwen"`
- `storage_keys` (object, required): MinIO storage keys for input images
  - For Flux: `user_image`, `user_mask`, `garment_image` (all required)
  - For Qwen: `masked_user_image`, `garment_image` (both required)
- `config` (object, optional): Model configuration parameters
  - Common: `seed` (integer), `steps` (integer)
  - Flux-specific: `guidance_scale` (float)

**Response** (201 Created):
```json
{
  "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd",
  "status": "QUEUED"
}
```

**Response Fields**:
- `job_id` (string): Job identifier (same as provided in request)
- `status` (string): Initial job status - always `"QUEUED"`

**Error Responses**:
- `400 Bad Request`: 
  - Provider disabled
  - Missing required fields
  - Invalid provider value
  - Missing required storage keys for provider
- `401 Unauthorized`: Invalid or missing `X-Internal-Auth` header
- `503 Service Unavailable`: Internal server error

**Example (cURL)**:
```bash
curl -X POST "http://cpu-bridge-host:8080/bridge/tryon" \
  -H "X-Internal-Auth: your-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd",
    "user_id": "user-123",
    "session_id": "session-456",
    "provider": "flux",
    "storage_keys": {
      "user_image": "fashionx-storage/.../user.png",
      "user_mask": "fashionx-storage/.../mask.png",
      "garment_image": "fashionx-storage/.../garment.png"
    },
    "config": {"seed": 42, "steps": 30}
  }'
```

---

### 2. GET /bridge/tryon/{job_id}

**Description**: Get the current status and details of a VTON job.

**Method**: `GET`

**Path**: `/bridge/tryon/{job_id}`

**Path Parameters**:
- `job_id` (string, required): Job identifier (UUID)

**Headers**:
```
X-Internal-Auth: <GATEWAY_TO_BRIDGE_SECRET>
```

**Response** (200 OK):
```json
{
  "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd",
  "user_id": "user-123",
  "session_id": "session-456",
  "provider": "flux",
  "status": "SUCCESS",
  "output_image_url": "https://example.com/output/image.png",
  "error": null,
  "gpu_node_id": "flux-lb",
  "created_at": "2025-12-02T10:00:00Z",
  "started_at": "2025-12-02T10:00:01Z",
  "finished_at": "2025-12-02T10:00:30Z"
}
```

**Response Fields**:
- `job_id` (string): Job identifier
- `user_id` (string): User identifier
- `session_id` (string): Session identifier
- `provider` (string): Provider type (`"flux"` or `"qwen"`)
- `status` (string): Job status - see [Status Values](#status-values)
- `output_image_url` (string, nullable): URL to output image (present if `status == "SUCCESS"`)
- `error` (string, nullable): Error message (present if `status == "FAILED"` or `"TIMEOUT"`)
- `gpu_node_id` (string, nullable): Load Balancer identifier
- `created_at` (string): Job creation timestamp (ISO 8601)
- `started_at` (string, nullable): Job start timestamp (ISO 8601)
- `finished_at` (string, nullable): Job completion timestamp (ISO 8601)

**Status Values**:
- `QUEUED`: Job is in queue, waiting to be processed
- `RUNNING`: Job accepted by Load Balancer, being processed by GPU server
- `SUCCESS`: Job completed successfully
- `FAILED`: Job failed (check `error` field for details)
- `TIMEOUT`: Job timed out

**Error Responses**:
- `401 Unauthorized`: Invalid or missing `X-Internal-Auth` header
- `404 Not Found`: Job not found
- `503 Service Unavailable`: Internal server error

**Example (cURL)**:
```bash
curl -X GET "http://cpu-bridge-host:8080/bridge/tryon/dd1283e6-91a9-4f40-851e-8687a5d557dd" \
  -H "X-Internal-Auth: your-secret"
```

---

### 3. GET /health

**Description**: Health check endpoint to verify service and dependency status.

**Method**: `GET`

**Path**: `/health`

**Headers**: None required

**Response** (200 OK):
```json
{
  "status": "ok",
  "db_connected": false,
  "kafka_connected": false,
  "minio_connected": true,
  "lb_reachable": true,
  "timestamp": "2025-12-02T10:00:00Z"
}
```

**Response Fields**:
- `status` (string): Overall status - `"ok"` or `"degraded"`
- `db_connected` (boolean): Always `false` (database removed)
- `kafka_connected` (boolean): Always `false` (Kafka removed)
- `minio_connected` (boolean): MinIO connection status
- `lb_reachable` (boolean): Load Balancer reachability (at least one enabled provider)
- `timestamp` (string): Health check timestamp (ISO 8601)

**Example (cURL)**:
```bash
curl -X GET "http://cpu-bridge-host:8080/health"
```

---

### 3. GET /metrics

**Description**: Prometheus metrics endpoint for monitoring.

**Method**: `GET`

**Path**: `/metrics`

**Headers**: None required

**Response** (200 OK):
```
# CPU Bridge Metrics
vton_queue_size{provider="flux"} 5
vton_queue_size{provider="qwen"} 2
vton_jobs_enqueued_total{provider="flux"} 150
vton_jobs_enqueued_total{provider="qwen"} 75
vton_jobs_dequeued_total{provider="flux"} 145
vton_jobs_dequeued_total{provider="qwen"} 73
```

**Metrics**:
- `vton_queue_size{provider="flux|qwen"}`: Current queue size
- `vton_jobs_enqueued_total{provider="flux|qwen"}`: Total jobs enqueued
- `vton_jobs_dequeued_total{provider="flux|qwen"}`: Total jobs dequeued

**Example (cURL)**:
```bash
curl -X GET "http://cpu-bridge-host:8080/metrics"
```

---

### 4. GET /

**Description**: Root endpoint with service information.

**Method**: `GET`

**Path**: `/`

**Headers**: None required

**Response** (200 OK):
```json
{
  "service": "CPU Bridge",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Load Balancer Integration

CPU Bridge uses the Load Balancer to select GPU nodes, then dispatches jobs directly to GPU servers.

### 1. Select GPU Node

CPU Bridge calls the Load Balancer to get an available GPU node.

**Endpoint**: `GET {LB_BASE_URL}/select_node?model={provider}`

**Method**: `GET`

**Headers**:
```
X-Internal-Auth: <BRIDGE_TO_GPU_SECRET>  (if auth enabled)
```

**Query Parameters**:
- `model` (required): Provider name - `"flux"` or `"qwen"`

**Response (200 OK)**:
```json
{
  "node_url": "http://10.0.0.11:8000",
  "node_id": "flux-gpu-1",
  "model": "flux"
}
```

**Response (503 Service Unavailable)** - No Available Nodes:
```json
{
  "error": "NO_AVAILABLE_NODE",
  "detail": "No available nodes for this model"
}
```

Other 503 error types:
- `NO_LIVE_NODE`: All nodes are dead
- `NO_HOT_NODE`: Nodes exist but not ready

**Behavior**:
- CPU Bridge calls `/select_node` to get a GPU node URL
- If **503 (no nodes)**: CPU Bridge waits `retry_delay_seconds` and calls `/select_node` again **infinitely** until a node becomes available
- If **200 (node selected)**: CPU Bridge dispatches job directly to the GPU node
- If GPU returns **any error** (429, 400, 401, 500, connection errors, etc.): CPU Bridge calls `/select_node` again to get a different node and retries **infinitely** until a GPU accepts

---

### 2. Dispatch to GPU Server

After getting a node from LB, CPU Bridge dispatches the job directly to the GPU server.

**Endpoint**: `POST {node_url}/tryon`

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Headers**:
```
X-Internal-Auth: <BRIDGE_TO_GPU_SECRET>
```

**Request Format**:

The request is sent as `multipart/form-data` with the following fields:

#### Form Fields (All Providers)

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `job_id` | string (UUID) | Yes | Unique job identifier generated by CPU Bridge |
| `user_id` | string | Yes | User ID from the original request |
| `session_id` | string (UUID) | Yes | Session ID from the original request |
| `provider` | string | Yes | Provider type - `"flux"` or `"qwen"` |
| `config` | string (JSON) | Yes | Model configuration as JSON string (e.g., `'{"seed": 42, "steps": 30, "guidance_scale": 5.0}'`) |

#### File Fields (Flux Provider)

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `user_image` | file (image/png) | Yes | User image file |
| `user_mask` | file (image/png) | Yes | User mask file |
| `garment_image` | file (image/png) | Yes | Garment image file |

#### File Fields (Qwen Provider)

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `masked_user_image` | file (image/png) | Yes | Masked user image file |
| `garment_image` | file (image/png) | Yes | Garment image file |

### Example Request (Flux)

**Using cURL**:
```bash
# First, get GPU node from LB
curl -X GET "http://lb-host:9000/select_node?model=flux" \
  -H "X-Internal-Auth: your-secret"

# Response: {"node_url": "http://10.0.0.11:8000", "node_id": "flux-gpu-1"}

# Then, dispatch to GPU server
curl -X POST "http://10.0.0.11:8000/tryon" \
  -H "X-Internal-Auth: your-secret" \
  -F "job_id=dd1283e6-91a9-4f40-851e-8687a5d557dd" \
  -F "user_id=user-123" \
  -F "session_id=session-456" \
  -F "provider=flux" \
  -F "config={\"seed\": 42, \"steps\": 30, \"guidance_scale\": 5.0}" \
  -F "user_image=@/path/to/user.png" \
  -F "user_mask=@/path/to/mask.png" \
  -F "garment_image=@/path/to/garment.png"
```

**Using Python requests**:
```python
import requests
from io import BytesIO

# Step 1: Get GPU node from LB
lb_url = "http://lb-host:9000"
lb_response = requests.get(
    f"{lb_url}/select_node",
    params={"model": "flux"},
    headers={"X-Internal-Auth": "your-secret"}
)
node_info = lb_response.json()
node_url = node_info["node_url"]  # e.g., "http://10.0.0.11:8000"

# Step 2: Dispatch to GPU server
url = f"{node_url}/tryon"
headers = {
    "X-Internal-Auth": "your-secret"
}

data = {
    "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd",
    "user_id": "user-123",
    "session_id": "session-456",
    "provider": "flux",
    "config": '{"seed": 42, "steps": 30, "guidance_scale": 5.0}'
}

files = {
    "user_image": ("user_image.png", BytesIO(user_image_bytes), "image/png"),
    "user_mask": ("user_mask.png", BytesIO(user_mask_bytes), "image/png"),
    "garment_image": ("garment_image.png", BytesIO(garment_image_bytes), "image/png")
}

response = requests.post(url, headers=headers, data=data, files=files)
```

### Response Codes (GPU Server)

| Status Code | Meaning | CPU Bridge Behavior |
|-------------|---------|---------------------|
| `202 Accepted` | Job accepted by GPU | Job removed from queue, marked as `RUNNING` |
| `429 Too Many Requests` | GPU server busy | Get different node from LB, retry **infinitely** |
| `400 Bad Request` | Invalid request | Get different node from LB, retry **infinitely** |
| `401 Unauthorized` | Auth failed | Get different node from LB, retry **infinitely** |
| `500 Internal Server Error` | Server error | Get different node from LB, retry **infinitely** |
| Connection errors | GPU not reachable | Get different node from LB, retry **infinitely** |
| Any other error | GPU error | Get different node from LB, retry **infinitely** |

**Note**: All GPU errors (except 202) trigger getting a different node from LB and retrying infinitely. If LB returns 503 (no nodes available), CPU Bridge keeps calling `/select_node` infinitely until a node becomes available.

### Response Codes (Load Balancer /select_node)

| Status Code | Meaning | CPU Bridge Behavior |
|-------------|---------|---------------------|
| `200 OK` | Node selected | Use returned `node_url` to dispatch job |
| `503 Service Unavailable` | No available nodes | CPU Bridge waits `retry_delay_seconds` and calls `/select_node` again **infinitely** until a node becomes available |

### Response Body (202 Accepted)

```json
{
  "status": "accepted",
  "message": "Job queued for processing",
  "job_id": "dd1283e6-91a9-4f40-851e-8687a5d557dd"
}
```

### Response Body (429 Too Many Requests)

```json
{
  "status": "busy",
  "message": "GPU server is currently busy",
  "retry_after": 5
}
```

### Retry Logic

**When LB returns 503 (no nodes available):**
1. CPU Bridge waits `retry_delay_seconds`
2. Calls LB `/select_node` again
3. Repeats step 1-2 **infinitely** until LB returns a node (200)

**When GPU server returns any error (429 busy, 400 bad request, 401 unauthorized, 500 server error, connection errors, etc.):**
1. CPU Bridge calls LB `/select_node` again to get a different GPU node
2. If LB returns 503, waits `retry_delay_seconds` and retries getting a node **infinitely**
3. If LB returns a node, dispatches job to the new GPU node
4. If new GPU also returns an error, repeats step 1-3 **infinitely** until a GPU accepts (202)

**All errors trigger infinite retries** - CPU Bridge will keep trying until a node becomes available and accepts the job.

### Load Balancer Configuration

Each provider has a single Load Balancer URL:

Configure in `configs/config.yaml`:
```yaml
providers:
  flux:
    load_balancer:
      url: "${FLUX_LB_URL:-http://localhost:9000}"
```

---

## Configuration

### Provider Enablement

Enable/disable providers in `configs/config.yaml`:

```yaml
providers:
  flux:
    enabled: true  # Set to false to disable
    load_balancer:
      url: "http://flux-lb:8080"
    retry_delay_seconds: 5  # Delay before retry after 503 (no nodes) response
  
  qwen:
    enabled: false  # Disabled provider rejects requests immediately
```

### Retry Configuration

Configure retry delay after 503 (no nodes) responses:

```yaml
providers:
  flux:
    retry_delay_seconds: 5  # Wait 5 seconds before retry when no nodes available
```

**Note**: Both 503 (no nodes) and 429 (busy) responses retry **infinitely**:
- **503**: Job stays in queue, retried after `retry_delay_seconds`
- **429**: CPU Bridge continuously gets different nodes from LB until one accepts

---

## Error Handling

### Provider Disabled

If a provider is disabled, requests are rejected immediately:

```json
{
  "detail": "Provider 'qwen' is disabled"
}
```

### Queue Full

If queue is full, job is still created in database but not enqueued. It will be picked up when queue space is available.

### Load Balancer Failures

- **503 No Available Nodes** → CPU Bridge waits `retry_delay_seconds` and calls `/select_node` again **infinitely** until a node becomes available
- **Other LB errors** → Job marked as `FAILED`

### GPU Server Failures

- **202 Accepted** → Job removed from queue, marked as `RUNNING`
- **429 Too Many Requests** → CPU Bridge gets different node from LB and retries **infinitely**
- **400 Bad Request** → CPU Bridge gets different node from LB and retries **infinitely**
- **401 Unauthorized** → CPU Bridge gets different node from LB and retries **infinitely**
- **500 Server Error** → CPU Bridge gets different node from LB and retries **infinitely**
- **Connection Errors** → CPU Bridge gets different node from LB and retries **infinitely**
- **Any Other Error** → CPU Bridge gets different node from LB and retries **infinitely**

**All GPU errors trigger infinite retries with different nodes**. If LB returns 503 (no nodes available), CPU Bridge keeps calling `/select_node` infinitely until a node becomes available.

---

## Example Integration (Python)

```python
import requests
import time

BASE_URL = "http://cpu-bridge-host:8080"
AUTH_HEADER = "your-secret"

# Create job
response = requests.post(
    f"{BASE_URL}/bridge/tryon",
    headers={"X-Internal-Auth": AUTH_HEADER},
    json={
        "user_id": "user-123",
        "session_id": "session-456",
        "provider": "flux",
        "storage_keys": {
            "user_image": "fashionx-storage/.../user.png",
            "user_mask": "fashionx-storage/.../mask.png",
            "garment_image": "fashionx-storage/.../garment.png"
        },
        "config": {"seed": 42, "steps": 30}
    }
)
job = response.json()
job_id = job["job_id"]

# Poll for status
while True:
    response = requests.get(
        f"{BASE_URL}/bridge/tryon/{job_id}",
        headers={"X-Internal-Auth": AUTH_HEADER}
    )
    status = response.json()
    
    if status["status"] in ["SUCCESS", "FAILED", "TIMEOUT"]:
        break
    
    time.sleep(2)
```

---

## Troubleshooting

### Jobs Stuck in QUEUED

- Check if provider is enabled
- Verify Load Balancer URLs are correct
- Check scheduler logs for errors
- Verify MinIO connectivity (images must be downloadable)

### Jobs Failing Immediately

- Check Load Balancer authentication (`BRIDGE_TO_GPU_SECRET`)
- Verify Load Balancer endpoints are reachable
- Check MinIO access (read permissions on bucket)
