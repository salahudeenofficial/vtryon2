# Postman Request Formats

Complete guide for testing GPU server endpoints with Postman.

## Base URL

```
http://localhost:8000
```

Or your server URL if deployed.

---

## 1. POST /tryon

Virtual try-on inference endpoint.

### Request Setup

**Method:** `POST`

**URL:** `http://localhost:8000/tryon`

**Headers:**
```
X-Internal-Auth: TEST_BRIDGE_TO_GPU_SECRET
```

> **Note:** Replace `TEST_BRIDGE_TO_GPU_SECRET` with your actual token from `configs/config.yaml` → `security.internal_auth_token`

**Body Type:** `form-data` (multipart/form-data)

### Form Data Fields

| Key | Type | Value | Required |
|-----|------|-------|----------|
| `job_id` | Text | `550e8400-e29b-41d4-a716-446655440000` | ✅ Yes |
| `user_id` | Text | `user123` | ✅ Yes |
| `session_id` | Text | `550e8400-e29b-41d4-a716-446655440001` | ✅ Yes |
| `provider` | Text | `qwen` | ✅ Yes |
| `masked_user_image` | File | Select PNG/JPEG image file | ✅ Yes |
| `garment_image` | File | Select PNG/JPEG image file | ✅ Yes |
| `config` | Text | `{"prompt": "将图片 1 中的绿色遮罩区域仅用于判断服装属于上半身或下半身，不要将服装限制在遮罩范围内。\n\n将图片 2 中的服装自然地穿戴到图片 1 中的人物身上，保持图片 2 中服装的完整形状、袖长和轮廓。无论图片 2 是单独的服装图还是人物穿着该服装的图，都应准确地转移服装，同时保留其原始面料质感、材质细节和颜色准确性。\n\n确保图片 1 中人物的面部、头发和皮肤完全保持不变。光照与阴影应自然匹配图片 1 的环境，但服装的材质外观必须忠实于图片 2。\n\n保持边缘平滑融合、阴影逼真，整体效果自然且不改变人物的身份特征", "seed": 42, "steps": 4, "cfg": 1.0}` | ✅ Yes |

### Example Config JSON

```json
{
  "prompt": "将图片 1 中的绿色遮罩区域仅用于判断服装属于上半身或下半身，不要将服装限制在遮罩范围内。\n\n将图片 2 中的服装自然地穿戴到图片 1 中的人物身上，保持图片 2 中服装的完整形状、袖长和轮廓。无论图片 2 是单独的服装图还是人物穿着该服装的图，都应准确地转移服装，同时保留其原始面料质感、材质细节和颜色准确性。\n\n确保图片 1 中人物的面部、头发和皮肤完全保持不变。光照与阴影应自然匹配图片 1 的环境，但服装的材质外观必须忠实于图片 2。\n\n保持边缘平滑融合、阴影逼真，整体效果自然且不改变人物的身份特征",
  "seed": 42,
  "steps": 4,
  "cfg": 1.0
}
```

### Success Response (202 Accepted)

```json
{
  "status": "accepted",
  "message": "Job queued for processing",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Responses

**429 Too Many Requests (GPU Busy):**
```json
{
  "status": "busy",
  "message": "GPU server is currently busy",
  "retry_after": 5
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or missing X-Internal-Auth header"
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid provider: <provider>. Must be 'qwen'"
}
```

### Postman Steps

1. Create new request → POST
2. Enter URL: `http://localhost:8000/tryon`
3. Go to **Headers** tab:
   - Add: `X-Internal-Auth` = `TEST_BRIDGE_TO_GPU_SECRET`
4. Go to **Body** tab:
   - Select `form-data`
   - Add each field:
     - `job_id` (Text): `550e8400-e29b-41d4-a716-446655440000`
     - `user_id` (Text): `user123`
     - `session_id` (Text): `550e8400-e29b-41d4-a716-446655440001`
     - `provider` (Text): `qwen`
     - `masked_user_image` (File): Click "Select Files" and choose image
     - `garment_image` (File): Click "Select Files" and choose image
     - `config` (Text): Paste the JSON config string
5. Click **Send**

---

## 2. GET /test

Readiness probe endpoint for Load Balancer.

### Request Setup

**Method:** `GET`

**URL:** `http://localhost:8000/test`

**Headers:** None required

### Success Response (200 OK)

**When Ready (Hot):**
```json
{
  "status": "hot",
  "model_loaded": true,
  "node_id": "qwen-gpu-1",
  "model_type": "qwen"
}
```

**When Not Ready (Loading):**
```json
{
  "status": "loading",
  "model_loaded": false,
  "node_id": "qwen-gpu-1"
}
```

### Postman Steps

1. Create new request → GET
2. Enter URL: `http://localhost:8000/test`
3. No headers needed
4. Click **Send**

---

## 3. GET /health

Liveness probe endpoint for Load Balancer.

### Request Setup

**Method:** `GET`

**URL:** `http://localhost:8000/health`

**Headers:** None required

### Success Response (200 OK)

```json
{
  "status": "ok",
  "model_loaded": true,
  "node_id": "qwen-gpu-1"
}
```

### Postman Steps

1. Create new request → GET
2. Enter URL: `http://localhost:8000/health`
3. No headers needed
4. Click **Send**

---

## Testing Scenarios

### Scenario 1: Test Health Endpoints

1. Send `GET /health` → Should return `200 OK`
2. Send `GET /test` → Should return `200 OK` with `"status": "hot"` if models loaded

### Scenario 2: Test Tryon Endpoint

1. Send `POST /tryon` with valid data → Should return `202 Accepted`
2. Immediately send another `POST /tryon` → Should return `429 Too Many Requests`
3. While inference is running, send `GET /health` → Should still return `200 OK` instantly
4. While inference is running, send `GET /test` → Should still return `200 OK` instantly

### Scenario 3: Test Authentication

1. Send `POST /tryon` without `X-Internal-Auth` header → Should return `401 Unauthorized`
2. Send `POST /tryon` with wrong auth token → Should return `401 Unauthorized`

### Scenario 4: Test Invalid Provider

1. Send `POST /tryon` with `provider: "invalid"` → Should return `400 Bad Request`

---

## Quick Test Collection

### Postman Collection JSON

```json
{
  "info": {
    "name": "GPU Server Qwen",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    },
    {
      "name": "Readiness Test",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/test",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["test"]
        }
      }
    },
    {
      "name": "Tryon Inference",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "X-Internal-Auth",
            "value": "TEST_BRIDGE_TO_GPU_SECRET",
            "type": "text"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "job_id",
              "value": "550e8400-e29b-41d4-a716-446655440000",
              "type": "text"
            },
            {
              "key": "user_id",
              "value": "user123",
              "type": "text"
            },
            {
              "key": "session_id",
              "value": "550e8400-e29b-41d4-a716-446655440001",
              "type": "text"
            },
            {
              "key": "provider",
              "value": "qwen",
              "type": "text"
            },
            {
              "key": "masked_user_image",
              "type": "file",
              "src": []
            },
            {
              "key": "garment_image",
              "type": "file",
              "src": []
            },
            {
              "key": "config",
              "value": "{\"prompt\": \"将图片 1 中的绿色遮罩区域仅用于判断服装属于上半身或下半身，不要将服装限制在遮罩范围内。\\n\\n将图片 2 中的服装自然地穿戴到图片 1 中的人物身上，保持图片 2 中服装的完整形状、袖长和轮廓。无论图片 2 是单独的服装图还是人物穿着该服装的图，都应准确地转移服装，同时保留其原始面料质感、材质细节和颜色准确性。\\n\\n确保图片 1 中人物的面部、头发和皮肤完全保持不变。光照与阴影应自然匹配图片 1 的环境，但服装的材质外观必须忠实于图片 2。\\n\\n保持边缘平滑融合、阴影逼真，整体效果自然且不改变人物的身份特征\", \"seed\": 42, \"steps\": 4, \"cfg\": 1.0}",
              "type": "text"
            }
          ]
        },
        "url": {
          "raw": "http://localhost:8000/tryon",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["tryon"]
        }
      }
    }
  ]
}
```

You can import this JSON into Postman to create a ready-to-use collection.

---

## Notes

- **Auth Token**: Get your actual token from `configs/config.yaml` → `security.internal_auth_token`
- **File Uploads**: Use PNG or JPEG images for `masked_user_image` and `garment_image`
- **Config Field**: Must be a JSON string (not a JSON object in Postman)
- **Response Time**: `/health` and `/test` should respond in < 1ms even during inference
- **429 Response**: Second `/tryon` request should return 429 in < 10ms

