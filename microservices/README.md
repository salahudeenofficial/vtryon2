# Microservices Architecture

## Overview
This repository contains microservices split from the monolithic ComfyUI workflow. Each service is independent with its own dependencies and can be deployed separately.

## Deployment Options

This architecture supports multiple deployment strategies:

### 1. **NVIDIA Triton Inference Server**
- Optimized ML model serving
- High throughput with GPU acceleration
- Ensemble models for full pipeline
- See: [TRITON_CONFIG.md](TRITON_CONFIG.md)

### 2. **Kafka-based Orchestration**
- Async message-driven workflow
- High throughput and fault tolerance
- Dead letter queue for error handling
- See: [KAFKA_SCHEMAS.md](KAFKA_SCHEMAS.md)

### 3. **Kubernetes Orchestration**
- Containerized deployment and scaling
- Auto-scaling with HPA
- Service discovery and load balancing
- See: [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md)

### 4. **Hybrid Approach (Recommended)**
- Triton for model inference
- Kafka for workflow orchestration
- Kubernetes for container orchestration

See: [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md) for detailed comparison

## Service Structure

```
microservices/
├── latent_encoder/      # Service 1: Image to Latent encoding
│   ├── API.md           # API specification
│   ├── requirements.txt
│   └── Dockerfile
├── text_encoder/        # Service 2: Text and Image encoding
│   ├── API.md
│   ├── requirements.txt
│   └── Dockerfile
├── sampling/            # Service 3: Diffusion sampling
│   ├── API.md
│   ├── requirements.txt
│   └── Dockerfile
├── decoding/            # Service 4: Latent to Image decoding
│   ├── API.md
│   ├── requirements.txt
│   └── Dockerfile
├── shared_utils/        # Shared utilities library
└── model_loader/        # Optional: Model loading service
```

## Multi-Protocol Support

Each service supports:
- **REST API** - HTTP/JSON for synchronous requests
- **gRPC** - For Triton Integration
- **Kafka** - Async message queue processing
- **File-based** - Batch processing via file system

See: [API_MULTI_PROTOCOL.md](API_MULTI_PROTOCOL.md)

## Architecture Document Issues Found

See [ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md) for detailed analysis of issues and missing components.

### Key Issues:
1. **Missing Model Dependencies**: Architecture doesn't specify model loading requirements
2. **Missing Input Parameters**: Sampling parameters, output paths not documented
3. **Missing Output Formats**: No specification of serialization format for tensors
4. **Missing Model Transformation**: ModelSamplingAuraFlow and CFGNorm steps not documented
5. **Shared Dependencies**: VAE model used by multiple services - need strategy

Quick reference: [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md)

## Quick Start

### Local Development with Docker Compose
```bash
docker-compose up -d
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/ -n vtryon
```

### Triton Inference Server
```bash
docker run --gpus all -p 8000:8000 -p 8001:8001 \
  -v $(pwd)/triton_models:/models \
  nvcr.io/nvidia/tritonserver:latest-py3 \
  tritonserver --model-repository=/models
```

## Next Steps

1. ✅ Created directory structure
2. ✅ Created API documentation for each service
3. ✅ Created requirements.txt for each service
4. ✅ Created deployment configurations (Docker, K8s, Triton, Kafka)
5. ⏳ Implement each microservice
6. ⏳ Create shared_utils package
7. ⏳ Define inter-service communication protocol
8. ⏳ Create Dockerfiles for each service
9. ⏳ Set up orchestration configuration


