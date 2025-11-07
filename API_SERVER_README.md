# Virtual Try-On API Server

FastAPI server for virtual try-on service using masked images and ComfyUI workflow.

## Installation

1. Install additional dependencies:
```bash
pip install -r mask.txt
```

2. Ensure all models are downloaded (see main README)

## Running the Server

```bash
python api_server.py
```

Or with uvicorn directly:
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### POST /tryon_extracted

Virtual try-on endpoint that:
1. Receives an image, mask_type, and prompt
2. Calls `masked_image()` from `mask.py` to create masked person image
3. Runs `workflow_script_serial.py` with the masked image and prompt
4. Returns the generated image

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Parameters:
  - `image` (file): Input person image (PNG/JPEG)
  - `mask_type` (string): One of `upper_body`, `lower_body`, or `other`
  - `prompt` (string): Text prompt for virtual try-on

**Response:**
- Content-Type: image/png
- Body: Generated try-on image file

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/tryon_extracted" \
  -F "image=@person.jpg" \
  -F "mask_type=upper_body" \
  -F "prompt=by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/tryon_extracted"
files = {"image": open("person.jpg", "rb")}
data = {
    "mask_type": "upper_body",
    "prompt": "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1."
}

response = requests.post(url, files=files, data=data)
with open("output.png", "wb") as f:
    f.write(response.content)
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Notes

- The server uses POST for file uploads (standard for multipart/form-data)
- Temporary files are automatically cleaned up after processing
- The `cloth.png` image must be present in the `input/` directory
- Generated images are saved in the `output/` directory
- The server includes CORS middleware (configure origins in production)

## Error Handling

The API returns appropriate HTTP status codes:
- `400`: Bad request (invalid mask_type, missing parameters)
- `500`: Internal server error (processing failed)

Error responses include a JSON body with error details.

