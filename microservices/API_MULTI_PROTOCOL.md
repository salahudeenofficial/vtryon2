# Microservices API - Multi-Protocol Support

## Protocol Support

Each microservice supports multiple communication protocols:

1. **REST API** - HTTP/JSON for synchronous requests
2. **gRPC** - For Triton Inference Server integration
3. **Kafka** - Async message queue processing
4. **File-based** - Batch processing via file system

---

## 1. LATENT_ENCODER Service

### REST API Endpoint
```
POST /api/v1/latent/encode
Content-Type: application/json

Request:
{
  "image_path": "/path/to/image.jpg",
  "vae_model_name": "qwen_image_vae.safetensors",
  "output_dir": "/path/to/output",
  "upscale_method": "lanczos",
  "megapixels": 1.0
}

Response:
{
  "status": "success",
  "request_id": "uuid-here",
  "latent_file_path": "/path/to/output/latent_123.pt",
  "latent_shape": [1, 4, 64, 64],
  "metadata": {...}
}
```

### gRPC (Triton)
```protobuf
service LatentEncoder {
  rpc EncodeImage(EncodeRequest) returns (EncodeResponse);
}

message EncodeRequest {
  string image_path = 1;
  string vae_model_name = 2;
  string output_dir = 3;
}

message EncodeResponse {
  string latent_file_path = 1;
  repeated int32 latent_shape = 2;
}
```

### Kafka Message
```json
{
  "request_id": "uuid",
  "service": "latent_encoder",
  "input": {
    "image_path": "/path/to/image.jpg",
    "vae_model_name": "qwen_image_vae.safetensors"
  },
  "output": {
    "topic": "latent-encoder-responses",
    "key": "request_id"
  }
}
```

### File-based
- Input: `{input_dir}/request_{id}.json`
- Output: `{output_dir}/latent_{id}.pt` + `{output_dir}/metadata_{id}.json`

---

## 2. TEXT_ENCODER Service

### REST API Endpoint
```
POST /api/v1/text/encode
Content-Type: application/json

Request:
{
  "image1_path": "/path/to/masked_person.jpg",
  "image2_path": "/path/to/cloth.png",
  "prompt": "by using the green masked area...",
  "negative_prompt": "",
  "clip_model_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
  "vae_model_name": "qwen_image_vae.safetensors"
}

Response:
{
  "status": "success",
  "request_id": "uuid-here",
  "positive_encoding_file": "/path/to/positive_enc.pt",
  "negative_encoding_file": "/path/to/negative_enc.pt",
  "positive_shape": [1, 77, 2048],
  "negative_shape": [1, 77, 2048]
}
```

### Kafka Message
```json
{
  "request_id": "uuid",
  "service": "text_encoder",
  "input": {
    "image1_path": "/path/to/image1.jpg",
    "image2_path": "/path/to/image2.png",
    "prompt": "...",
    "negative_prompt": ""
  }
}
```

---

## 3. SAMPLING Service

### REST API Endpoint
```
POST /api/v1/sampling/sample
Content-Type: application/json

Request:
{
  "positive_encoding_file": "/path/to/positive.pt",
  "negative_encoding_file": "/path/to/negative.pt",
  "latent_file": "/path/to/latent.pt",
  "unet_model_name": "qwen_image_edit_2509_fp8_e4m3fn.safetensors",
  "lora_model_name": "Qwen-Image-Lightning-4steps-V2.0.safetensors",
  "sampling_params": {
    "seed": 12345,
    "steps": 4,
    "cfg": 1.0,
    "sampler_name": "euler",
    "scheduler": "simple",
    "denoise": 1.0
  },
  "model_transform_params": {
    "shift": 3,
    "strength": 1.0
  }
}

Response:
{
  "status": "success",
  "request_id": "uuid-here",
  "sampled_latent_file": "/path/to/sampled_latent.pt",
  "sampled_latent_shape": [1, 4, 64, 64],
  "sampling_metadata": {...}
}
```

### Kafka Message
```json
{
  "request_id": "uuid",
  "service": "sampling",
  "input": {
    "positive_encoding_file": "/path/to/positive.pt",
    "negative_encoding_file": "/path/to/negative.pt",
    "latent_file": "/path/to/latent.pt",
    "sampling_params": {...}
  }
}
```

---

## 4. DECODING Service

### REST API Endpoint
```
POST /api/v1/decoding/decode
Content-Type: application/json

Request:
{
  "latent_file": "/path/to/sampled_latent.pt",
  "vae_model_name": "qwen_image_vae.safetensors",
  "output_filename": "test_male_1",
  "output_dir": "/path/to/output",
  "output_format": "jpg"
}

Response:
{
  "status": "success",
  "request_id": "uuid-here",
  "image_file_path": "/path/to/output/test_male_1_123.jpg",
  "image_shape": [1024, 1024, 3],
  "file_size": 245678
}
```

### Kafka Message
```json
{
  "request_id": "uuid",
  "service": "decoding",
  "input": {
    "latent_file": "/path/to/latent.pt",
    "output_filename": "test_male_1",
    "output_format": "jpg"
  }
}
```

---

## Protocol Selection Guide

### Use REST API when:
- Synchronous processing required
- Low latency needed
- Simple request/response
- Direct integration

### Use gRPC (Triton) when:
- Maximum throughput needed
- Model optimization required
- GPU acceleration needed
- Batch processing important

### Use Kafka when:
- Async processing acceptable
- High throughput required
- Workflow orchestration needed
- Fault tolerance important

### Use File-based when:
- Batch processing
- Legacy system integration
- Large data volumes
- Offline processing

---

## Error Response Format (All Protocols)

```json
{
  "status": "error",
  "request_id": "uuid-here",
  "error_code": "MODEL_NOT_FOUND",
  "error_message": "VAE model not found: qwen_image_vae.safetensors",
  "timestamp": "2024-11-06T12:00:00Z"
}
```

Common Error Codes:
- `MODEL_NOT_FOUND`: Model file not found
- `IMAGE_NOT_FOUND`: Input image file not found
- `INVALID_INPUT`: Invalid input parameters
- `ENCODING_FAILED`: Encoding process failed
- `SAMPLING_FAILED`: Sampling process failed
- `DECODING_FAILED`: Decoding process failed
- `OUTPUT_DIR_NOT_WRITABLE`: Cannot write to output directory

