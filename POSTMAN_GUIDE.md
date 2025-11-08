# Postman Testing Guide for Qwen Image Edit API

This guide explains how to test the Qwen Image Edit API using Postman.

## API Endpoint

**URL:** `http://localhost:8000/tryon` (or `http://YOUR_SERVER_IP:8000/tryon`)

**Method:** `POST`

## Request Setup in Postman

### Step 1: Create a New Request

1. Open Postman
2. Click **"New"** → **"HTTP Request"**
3. Set the method to **POST**
4. Enter the URL: `http://localhost:8000/tryon`

### Step 2: Configure Request Body

1. Click on the **"Body"** tab
2. Select **"form-data"** (not raw or x-www-form-urlencoded)
3. Add the following fields:

#### Required Fields:

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `masked_person_image` | **File** | Masked person image (PNG/JPEG) | Select a file |
| `cloth_image` | **File** | Cloth/garment image (PNG/JPEG) | Select a file |
| `prompt` | **Text** | Text prompt for virtual try-on | "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1." |

#### Optional Fields:

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `seed` | **Text** | Random seed for reproducibility | `724723345395306` |

### Step 3: Add Files

For `masked_person_image` and `cloth_image`:
1. Click on the field name
2. Change the type from **"Text"** to **"File"** (dropdown on the right)
3. Click **"Select Files"** and choose your image files

### Step 4: Add Prompt Text

For the `prompt` field:
1. Keep it as **"Text"** type
2. Enter your prompt text in the value field

### Step 5: Send Request

1. Click the **"Send"** button
2. Wait for the response (this may take 30-60 seconds depending on GPU)

## Expected Response

### Success Response (200 OK)

- **Content-Type:** `image/png`
- **Body:** Binary image data (the generated result image)
- **Headers:** 
  - `content-type: image/png`
  - `content-disposition: attachment; filename="qwen_xxxxx_00001_.png"`

**How to view the image in Postman:**
- The image will appear in the response body
- Click **"Save Response"** → **"Save to a file"** to download it
- Or use the **"Preview"** tab to view the image directly

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "mask_type must be one of ['upper_body', 'lower_body', 'other'], got 'invalid'"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "masked_person_image"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Error processing request: <error message>"
}
```

## Complete Postman Setup Example

### Visual Guide:

```
┌─────────────────────────────────────────────────┐
│ POST http://localhost:8000/tryon               │
├─────────────────────────────────────────────────┤
│ Body (form-data)                                │
├─────────────────────────────────────────────────┤
│ masked_person_image │ [File] │ [Select File]   │
│ cloth_image         │ [File] │ [Select File]   │
│ prompt              │ [Text] │ "your prompt..." │
│ seed (optional)     │ [Text] │ 724723345395306 │
└─────────────────────────────────────────────────┘
```

## Example cURL Command (for reference)

If you prefer using cURL, here's the equivalent command:

```bash
curl -X POST "http://localhost:8000/tryon" \
  -F "masked_person_image=@/path/to/masked_person.png" \
  -F "cloth_image=@/path/to/cloth.png" \
  -F "prompt=by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1." \
  -F "seed=724723345395306" \
  --output result.png
```

## Health Check Endpoint

You can also test the health endpoint:

**URL:** `http://localhost:8000/health`  
**Method:** `GET`

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "qwen_image_edit"
}
```

## Troubleshooting

### Issue: "Connection refused"
- **Solution:** Make sure the server is running. Check with `./setup.sh` or `python api_server.py`

### Issue: "Field required" error
- **Solution:** Make sure all required fields are set to the correct type:
  - `masked_person_image` and `cloth_image` must be **File** type
  - `prompt` must be **Text** type

### Issue: "422 Unprocessable Content"
- **Solution:** 
  - Verify all required fields are present
  - Check that file fields are set to **File** type, not **Text**
  - Ensure the prompt field is not empty

### Issue: Slow response or timeout
- **Solution:** 
  - The API processes images using GPU models, which can take 30-60 seconds
  - Increase Postman's timeout settings: Settings → General → Request timeout (set to 120 seconds or more)

### Issue: "Error processing request"
- **Solution:**
  - Check server logs for detailed error messages
  - Verify that models are downloaded (run `bash download.sh`)
  - Ensure input images are valid PNG/JPEG files
  - Check that the server has access to GPU (if required)

## Tips

1. **Save as Collection:** Save your request as a Postman Collection for easy reuse
2. **Environment Variables:** Create a Postman Environment with variables like:
   - `base_url`: `http://localhost:8000`
   - `api_endpoint`: `{{base_url}}/tryon`
3. **Pre-request Script:** You can add a pre-request script to generate unique filenames or timestamps
4. **Tests:** Add Postman tests to verify response status and image format

## Example Postman Collection JSON

You can import this into Postman:

```json
{
  "info": {
    "name": "Qwen Image Edit API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Try-On",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "masked_person_image",
              "type": "file",
              "src": []
            },
            {
              "key": "cloth_image",
              "type": "file",
              "src": []
            },
            {
              "key": "prompt",
              "type": "text",
              "value": "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
            },
            {
              "key": "seed",
              "type": "text",
              "value": "724723345395306"
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
    },
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
    }
  ]
}
```

