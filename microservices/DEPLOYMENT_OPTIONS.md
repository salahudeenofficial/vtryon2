# Microservices Architecture - Deployment Options

## Overview
This architecture supports multiple deployment strategies:
1. **NVIDIA Triton Inference Server** - For optimized ML model serving
2. **Kafka-based Orchestration** - For async message-driven workflow
3. **Kubernetes Orchestration** - For containerized deployment and scaling

## Architecture Compatibility Analysis

### 1. NVIDIA Triton Inference Server

#### Requirements
- Models must be exported in Triton-supported formats (ONNX, TensorRT, PyTorch)
- Each service needs model repository structure
- Input/output tensors must be defined
- Batch support for throughput optimization

#### Service Mapping
- **latent_encoder**: VAE encoder model → Triton model
- **text_encoder**: CLIP + Text encoder → Triton model  
- **sampling**: UNET + LoRA → Triton model
- **decoding**: VAE decoder → Triton model

#### Triton Model Repository Structure
```
triton_models/
├── latent_encoder/
│   ├── config.pbtxt
│   └── 1/
│       └── model.plan (TensorRT) or model.onnx
├── text_encoder/
│   ├── config.pbtxt
│   └── 1/
│       └── model.plan
├── sampling/
│   ├── config.pbtxt
│   └── 1/
│       └── model.plan
└── decoding/
    ├── config.pbtxt
    └── 1/
        └── model.plan
```

#### Considerations
- ComfyUI nodes are Python-based, need conversion to ONNX/TensorRT
- May need Python backend in Triton for custom nodes
- Model ensemble support for multi-step pipelines
- Dynamic batching for throughput

---

### 2. Kafka-based Orchestration

#### Requirements
- Message schema definition (Avro/JSON Schema)
- Topic structure for request/response
- Error handling and retry logic
- Dead letter queue for failed messages

#### Kafka Topic Structure
```
Topics:
- latent-encoder-requests    # Input: image paths
- latent-encoder-responses  # Output: latent paths
- text-encoder-requests    # Input: images + prompt
- text-encoder-responses    # Output: encoding paths
- sampling-requests         # Input: encodings + latent
- sampling-responses        # Output: sampled latent path
- decoding-requests         # Input: latent path
- decoding-responses        # Output: image path
- workflow-orchestrator     # Orchestrates full pipeline
```

#### Message Schema (Avro)
```json
{
  "type": "record",
  "name": "LatentEncoderRequest",
  "fields": [
    {"name": "request_id", "type": "string"},
    {"name": "image_path", "type": "string"},
    {"name": "vae_model_name", "type": "string"},
    {"name": "timestamp", "type": "long"}
  ]
}
```

#### Considerations
- Async processing requires correlation IDs
- Need to handle partial failures
- State management for multi-step workflows
- Message ordering guarantees

---

### 3. Kubernetes Orchestration

#### Requirements
- Container images for each service
- Deployment manifests with resource limits
- Service discovery (Kubernetes Services)
- ConfigMaps for configuration
- Secrets for models/credentials
- Horizontal Pod Autoscaler (HPA) for scaling

#### Kubernetes Resources Needed
- **Deployments**: One per microservice
- **Services**: ClusterIP for internal communication
- **ConfigMaps**: Model paths, parameters
- **PersistentVolumeClaims**: For model storage
- **Ingress**: For external API access (if needed)
- **HPA**: Auto-scaling based on CPU/memory

#### Resource Requirements
- GPU nodes for ML inference
- Shared storage for models
- Network policies for service isolation
- Service mesh (Istio/Linkerd) for advanced routing

---

## Deployment Strategy Comparison

| Feature | Triton Server | Kafka | Kubernetes |
|---------|--------------|-------|------------|
| **Model Serving** | ✅ Optimized | ❌ Need separate serving | ✅ Via containers |
| **Throughput** | ✅ Highest | ✅ High (async) | ✅ Scalable |
| **Latency** | ✅ Lowest | ⚠️ Higher (async) | ✅ Low |
| **Scalability** | ⚠️ Limited | ✅ Excellent | ✅ Excellent |
| **Complexity** | ⚠️ Medium | ⚠️ Medium | ⚠️ High |
| **Resource Efficiency** | ✅ Best | ✅ Good | ⚠️ Higher overhead |

---

## Hybrid Approach Recommendation

### Best Practice: Combine All Three

1. **Triton** for model inference (latent_encoder, text_encoder, sampling, decoding)
2. **Kafka** for workflow orchestration and async processing
3. **Kubernetes** for container orchestration and scaling

### Architecture Flow:
```
Kafka Producer → Workflow Orchestrator (K8s Pod)
    ↓
Triton Inference Server (K8s Deployment)
    ↓
Kafka Consumer → Save Results
```

---

## API Updates Required

Each service API needs to support:
1. **REST API** (for direct calls)
2. **gRPC** (for Triton)
3. **Kafka Messages** (for async processing)
4. **File-based I/O** (for batch processing)

---

## Next Steps

1. Create Triton model repository structure
2. Define Kafka message schemas
3. Create Kubernetes manifests
4. Create Dockerfiles for each service
5. Update API documentation with all deployment modes

