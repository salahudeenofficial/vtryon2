# Latent Encoder Microservice - Implementation API

## Purpose
Encodes input images to latent space representation for diffusion models. Supports **Kafka orchestration** and **standalone testing**.

## Service Modes

### Mode 1: Kafka Consumer (Production)
Listens to `latent-encoder-requests` topic, processes messages, publishes to `latent-encoder-responses`.

### Mode 2: Standalone Script (Development & Testing)
Direct Python script execution for development/testing without Kafka.

---

## Inputs

### Required:
- **image_path** (str): Path to the input image file (masked person image)
  - Supported formats: JPG, JPEG, PNG
  - Validation: File must exist and be readable

### Optional:
- **vae_model_name** (str): Name of the VAE model file (default: "qwen_image_vae.safetensors")
- **upscale_method** (str): Method for image scaling (default: "lanczos")
  - Options: "lanczos", "nearest", "bilinear", "bicubic"
- **megapixels** (float): Target megapixels for scaling (default: 1.0)
- **output_dir** (str): Directory to save outputs (default: "./output")
- **request_id** (str): Unique request identifier (auto-generated if not provided)

---

## Outputs

### Success Response:
```json
{
  "status": "success",
  "request_id": "uuid-here",
  "latent_file_path": "/path/to/output/latent_123_abc.pt",
  "latent_shape": [1, 4, 64, 64],
  "scaled_image_path": "/path/to/output/scaled_image_123.png",
  "metadata": {
    "original_image_shape": [1024, 1024, 3],
    "scaled_image_shape": [1024, 1024, 3],
    "latent_shape": [1, 4, 64, 64],
    "vae_model_name": "qwen_image_vae.safetensors",
    "processing_time_ms": 450,
    "timestamp": "2024-11-06T12:00:00Z"
  }
}
```

### Error Response:
```json
{
  "status": "error",
  "request_id": "uuid-here",
  "error_code": "IMAGE_NOT_FOUND",
  "error_message": "Image file not found: /path/to/image.jpg",
  "timestamp": "2024-11-06T12:00:00Z"
}
```

---

## Error Codes

- `IMAGE_NOT_FOUND`: Input image file does not exist
- `IMAGE_INVALID`: Image file is corrupted or invalid format
- `VAE_MODEL_NOT_FOUND`: VAE model file not found
- `ENCODING_FAILED`: VAE encoding process failed
- `OUTPUT_DIR_NOT_WRITABLE`: Cannot write to output directory
- `SCALING_FAILED`: Image scaling process failed

---

## Output Format

### Latent Tensor File
- **Format**: PyTorch tensor (`.pt` file)
- **Structure**: `torch.Tensor` with shape `[batch, channels, height, width]`
- **Example**: `latent_123_abc.pt` with shape `[1, 4, 64, 64]`
- **Serialization**: `torch.save(tensor, file_path)`

### Metadata File (Optional)
- **Format**: JSON
- **Name**: `{latent_filename}.json`
- **Contains**: Shape, model info, processing metadata

---

## Kafka Integration

### Request Topic: `latent-encoder-requests`
```json
{
  "request_id": "uuid-here",
  "correlation_id": "workflow-uuid",
  "image_path": "/path/to/masked_person.jpg",
  "vae_model_name": "qwen_image_vae.safetensors",
  "output_dir": "/path/to/output",
  "upscale_method": "lanczos",
  "megapixels": 1.0,
  "timestamp": 1234567890
}
```

### Response Topic: `latent-encoder-responses`
```json
{
  "request_id": "uuid-here",
  "correlation_id": "workflow-uuid",
  "status": "success",
  "latent_file_path": "/path/to/latent.pt",
  "latent_shape": [1, 4, 64, 64],
  "error_message": null,
  "timestamp": 1234567890
}
```

### Kafka Configuration
- **Bootstrap Servers**: `KAFKA_BOOTSTRAP_SERVERS` env var (default: "localhost:9092")
- **Consumer Group**: `latent-encoder-group`
- **Auto Offset Reset**: `earliest`
- **Enable Auto Commit**: `false` (manual commit after processing)

---

## Dependencies

### ComfyUI Nodes Required:
- `VAELoader` - Load VAE model
- `LoadImage` - Load input image
- `ImageScaleToTotalPixels` - Scale image (custom node)
- `VAEEncode` - Encode image to latent

### Python Packages:
- All packages from ComfyUI `requirements.txt` (torch, torchvision, etc.)
- **Additional packages**:
  - `confluent-kafka>=2.3.0` (for Kafka)
  - `python-dotenv>=1.0.0` (for config)

### Shared Utilities:
- `get_value_at_index()` - Extract values from ComfyUI outputs
- `find_path()` - Find ComfyUI directory
- `add_comfyui_directory_to_sys_path()` - Setup paths
- `add_extra_model_paths()` - Load extra paths
- `import_custom_nodes_minimal()` - Load custom nodes

---

## Implementation File Structure

```
latent_encoder/
├── API.md                    # This file
├── requirements.txt          # Only ADDITIONAL packages (not duplicates)
├── Dockerfile
├── README.md
├── .env.example
├── setup_comfyui.sh          # Script to copy ComfyUI files
├── main.py                   # Entry point (mode selector)
├── service.py                # Core service logic
├── kafka_handler.py         # Kafka consumer/producer
├── config.py                # Configuration management
├── models.py                # Data models (Pydantic)
├── errors.py                # Custom exceptions
├── utils.py                 # Utility functions
├── comfyui/                 # Copied ComfyUI files (symlink or copy)
│   ├── comfy/
│   ├── nodes.py
│   ├── folder_paths.py
│   ├── execution.py
│   ├── main.py
│   ├── utils/
│   ├── comfy_execution/
│   ├── comfy_extras/
│   └── custom_nodes/
└── tests/
    ├── test_service.py
    ├── test_kafka.py
    └── fixtures/
        └── test_images/
```

---

## Testing Strategy

### 1. Standalone Testing (Primary)
Test individual functions:
- Image loading
- Image scaling
- VAE encoding
- Error handling

### 2. Kafka Tests
Test Kafka integration:
- Message consumption
- Message production
- Error handling
- DLQ handling

---

## Example Usage

### Standalone Mode (Testing)
```bash
python main.py \
  --mode standalone \
  --image_path test_set/male/masked_person/1.jpg \
  --vae_model_name qwen_image_vae.safetensors \
  --output_dir ./output
```

### Kafka Mode
```bash
python main.py --mode kafka \
  --kafka-bootstrap-servers localhost:9092 \
  --request-topic latent-encoder-requests \
  --response-topic latent-encoder-responses
```

---

## Configuration via Environment Variables

```bash
# Service mode
MODE=kafka  # or "standalone"

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_REQUEST_TOPIC=latent-encoder-requests
KAFKA_RESPONSE_TOPIC=latent-encoder-responses
KAFKA_CONSUMER_GROUP=latent-encoder-group

# Models
MODEL_DIR=/models
VAE_MODEL_NAME=qwen_image_vae.safetensors

# Output
OUTPUT_DIR=/output

# ComfyUI
COMFYUI_PATH=/path/to/ComfyUI

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Processing Options
UPSCALE_METHOD=lanczos
MEGAPIXELS=1.0
```
