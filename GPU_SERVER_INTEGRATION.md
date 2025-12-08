# GPU Server Integration Guide

Complete guide for integrating GPU inference servers with FashionX Load Balancer v1.

## Overview

GPU servers must implement specific endpoints and callbacks to work with the load balancer. This guide covers all API requirements and request/response structures.

## Required Endpoints

### 1. GET /health (Liveness Probe)

**Purpose**: Indicates the server is running and reachable.

**Request:**
```
GET /health
```

**Response (200):**
```json
{
  "status": "ok",
  "model_loaded": true,
  "node_id": "qwen-gpu-1"
}
```

**Requirements:**
- Must respond within `health_timeout` seconds (default: 0.3s)
- Must return 200 status code
- Should indicate if model is loaded (`model_loaded: true/false`)

### 2. GET /test (Readiness Probe)

**Purpose**: Indicates the server is ready to handle inference requests.

**Request:**
```
GET /test
```

**Response (200) - When Ready:**
```json
{
  "status": "hot",
  "model_loaded": true,
  "node_id": "qwen-gpu-1",
  "model_type": "qwen"
}
```

**Response (200) - When Not Ready:**
```json
{
  "status": "loading",
  "model_loaded": false,
  "node_id": "qwen-gpu-1"
}
```

**Requirements:**
- Must respond within `health_timeout` seconds
- `model_loaded: true` is required for node to be marked HOT by load balancer
- Should accurately reflect model readiness

## Required Callbacks

### 1. POST /job_complete (to Load Balancer)

**Purpose**: Notify load balancer when job completes.

**When to Call:**
- After inference completes (success or failure)
- Should be called for every job that was started
- Call even if inference fails

**Request:**
```
POST http://<load-balancer-url>/job_complete
Content-Type: application/json
X-Internal-Auth: <auth-token>  (if auth enabled)
```

**Request Body:**
```json
{
  "node_id": "qwen-gpu-1",
  "job_id": "job-1234567890",
  "metadata": {}
}
```

**Response (200):**
```json
{
  "status": "ok"
}
```

**Requirements:**
- Call this endpoint after every job completion
- Use the `node_id` that matches your server
- Include `job_id` if available
- Set timeout to 2-5 seconds (don't block on this)

### 2. POST /heartbeat (to Load Balancer) - Optional

**Purpose**: Send periodic status updates.

**When to Call:**
- Every 10-30 seconds (recommended: 15 seconds)
- When busy state changes
- When model loading status changes

**Request:**
```
POST http://<load-balancer-url>/heartbeat
Content-Type: application/json
X-Internal-Auth: <auth-token>  (if auth enabled)
```

**Request Body:**
```json
{
  "node_id": "qwen-gpu-1",
  "metadata": {
    "busy": false,
    "active_jobs": 2,
    "status": "ready"
  }
}
```

**Response (200):**
```json
{
  "status": "ok"
}
```

**Requirements:**
- Optional but recommended
- Send periodically (every 15 seconds)
- Include current busy state in metadata
- Don't block on response

## Integration Checklist

- [ ] Implement `GET /health` endpoint
- [ ] Implement `GET /test` endpoint with `model_loaded` check
- [ ] Call `POST /job_complete` to LB after every job
- [ ] (Optional) Implement heartbeat to LB
- [ ] Configure `LB_URL` and `INTERNAL_AUTH` if needed
- [ ] Test endpoints respond within timeout (0.3s default)
- [ ] Verify node appears as HOT in LB after model loads

## Testing Integration

### 1. Test Health Endpoint

```bash
curl http://your-gpu-server:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "node_id": "qwen-gpu-1"
}
```

### 2. Test Readiness Endpoint

```bash
curl http://your-gpu-server:8000/test
```

**Expected Response (when ready):**
```json
{
  "status": "hot",
  "model_loaded": true,
  "node_id": "qwen-gpu-1",
  "model_type": "qwen"
}
```

### 3. Verify LB Detects Node

```bash
# Wait 5-10 seconds for health checker
curl http://localhost:9000/nodes?model=qwen | jq .
```

**Expected:** Node should appear with `"state": "hot"`

### 4. Test Job Completion Callback

```bash
# Manually test callback
curl -X POST http://localhost:9000/job_complete \
  -H "Content-Type: application/json" \
  -d '{"node_id": "qwen-gpu-1", "job_id": "test-123"}'
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

## Common Issues

### Node Not Becoming HOT

**Problem**: Node stays in RUNNING or DEAD state.

**Solutions**:
1. Verify `/test` returns `model_loaded: true`
2. Check response time is < `health_timeout` (default: 0.3s)
3. Verify network connectivity between LB and GPU server
4. Check LB logs for health check errors

### Job Completion Not Working

**Problem**: Heat keeps increasing, never decreases.

**Solutions**:
1. Verify `POST /job_complete` is called after every job
2. Check `LB_URL` is correct
3. Verify `INTERNAL_AUTH` matches LB config (if enabled)
4. Check network connectivity to LB
5. Review GPU server logs for callback errors

## Best Practices

1. **Always call `/job_complete`**: Even on errors, notify LB
2. **Fast health checks**: Keep `/health` and `/test` responses fast (< 100ms)
3. **Error handling**: Don't let callback failures break inference
4. **Logging**: Log all callbacks for debugging
5. **Timeout handling**: Set reasonable timeouts for LB callbacks (2-5 seconds)

## Configuration

### Load Balancer URL

Set the load balancer URL in your GPU server configuration:
- Default: `http://localhost:9000`
- Production: Use your LB server 