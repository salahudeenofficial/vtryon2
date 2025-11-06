# Triton Inference Server Configuration

## Model Repository Structure

```
triton_models/
├── latent_encoder/
│   ├── config.pbtxt
│   └── 1/
│       └── model.onnx (or model.plan for TensorRT)
├── text_encoder/
│   ├── config.pbtxt
│   └── 1/
│       └── model.onnx
├── sampling/
│   ├── config.pbtxt
│   └── 1/
│       └── model.onnx
└── decoding/
    ├── config.pbtxt
    └── 1/
        └── model.onnx
```

---

## 1. Latent Encoder Model Config

```protobuf
name: "latent_encoder"
platform: "onnxruntime_onnx"
max_batch_size: 8
input [
  {
    name: "input_image"
    data_type: TYPE_FP32
    dims: [ -1, 3, 1024, 1024 ]
  }
]
output [
  {
    name: "latent"
    data_type: TYPE_FP32
    dims: [ -1, 4, 64, 64 ]
  }
]
instance_group [
  {
    count: 1
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]
dynamic_batching {
  max_queue_delay_microseconds: 100
  preferred_batch_size: [ 1, 2, 4, 8 ]
}
```

---

## 2. Text Encoder Model Config

```protobuf
name: "text_encoder"
platform: "onnxruntime_onnx"
max_batch_size: 4
input [
  {
    name: "image1"
    data_type: TYPE_FP32
    dims: [ -1, 3, 1024, 1024 ]
  },
  {
    name: "image2"
    data_type: TYPE_FP32
    dims: [ -1, 3, 1024, 1024 ]
  },
  {
    name: "prompt"
    data_type: TYPE_STRING
    dims: [ 1 ]
  },
  {
    name: "negative_prompt"
    data_type: TYPE_STRING
    dims: [ 1 ]
  }
]
output [
  {
    name: "positive_encoding"
    data_type: TYPE_FP32
    dims: [ -1, 77, 2048 ]
  },
  {
    name: "negative_encoding"
    data_type: TYPE_FP32
    dims: [ -1, 77, 2048 ]
  }
]
instance_group [
  {
    count: 1
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]
```

---

## 3. Sampling Model Config

```protobuf
name: "sampling"
platform: "onnxruntime_onnx"
max_batch_size: 1
input [
  {
    name: "positive_encoding"
    data_type: TYPE_FP32
    dims: [ 1, 77, 2048 ]
  },
  {
    name: "negative_encoding"
    data_type: TYPE_FP32
    dims: [ 1, 77, 2048 ]
  },
  {
    name: "latent"
    data_type: TYPE_FP32
    dims: [ 1, 4, 64, 64 ]
  },
  {
    name: "seed"
    data_type: TYPE_INT64
    dims: [ 1 ]
  },
  {
    name: "steps"
    data_type: TYPE_INT32
    dims: [ 1 ]
  },
  {
    name: "cfg"
    data_type: TYPE_FP32
    dims: [ 1 ]
  }
]
output [
  {
    name: "sampled_latent"
    data_type: TYPE_FP32
    dims: [ 1, 4, 64, 64 ]
  }
]
instance_group [
  {
    count: 1
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]
```

---

## 4. Decoding Model Config

```protobuf
name: "decoding"
platform: "onnxruntime_onnx"
max_batch_size: 8
input [
  {
    name: "latent"
    data_type: TYPE_FP32
    dims: [ -1, 4, 64, 64 ]
  }
]
output [
  {
    name: "image"
    data_type: TYPE_FP32
    dims: [ -1, 3, 1024, 1024 ]
  }
]
instance_group [
  {
    count: 1
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]
dynamic_batching {
  max_queue_delay_microseconds: 100
  preferred_batch_size: [ 1, 2, 4, 8 ]
}
```

---

## 5. Ensemble Model (Full Pipeline)

```protobuf
name: "vtryon_pipeline"
platform: "ensemble"
max_batch_size: 1
input [
  {
    name: "image1"
    data_type: TYPE_FP32
    dims: [ 1, 3, 1024, 1024 ]
  },
  {
    name: "image2"
    data_type: TYPE_FP32
    dims: [ 1, 3, 1024, 1024 ]
  },
  {
    name: "prompt"
    data_type: TYPE_STRING
    dims: [ 1 ]
  }
]
output [
  {
    name: "output_image"
    data_type: TYPE_FP32
    dims: [ 1, 3, 1024, 1024 ]
  }
]
ensemble_scheduling {
  step [
    {
      model_name: "latent_encoder"
      model_version: -1
      input_map {
        key: "input_image"
        value: "image1"
      }
      output_map {
        key: "latent"
        value: "latent_enc"
      }
    },
    {
      model_name: "text_encoder"
      model_version: -1
      input_map {
        key: "image1"
        value: "image1"
      }
      input_map {
        key: "image2"
        value: "image2"
      }
      input_map {
        key: "prompt"
        value: "prompt"
      }
      output_map {
        key: "positive_encoding"
        value: "pos_enc"
      }
      output_map {
        key: "negative_encoding"
        value: "neg_enc"
      }
    },
    {
      model_name: "sampling"
      model_version: -1
      input_map {
        key: "positive_encoding"
        value: "pos_enc"
      }
      input_map {
        key: "negative_encoding"
        value: "neg_enc"
      }
      input_map {
        key: "latent"
        value: "latent_enc"
      }
      output_map {
        key: "sampled_latent"
        value: "sampled_lat"
      }
    },
    {
      model_name: "decoding"
      model_version: -1
      input_map {
        key: "latent"
        value: "sampled_lat"
      }
      output_map {
        key: "image"
        value: "output_image"
      }
    }
  ]
}
```

---

## Python Backend (For Custom ComfyUI Nodes)

If models can't be converted to ONNX, use Python backend:

```protobuf
name: "latent_encoder"
backend: "python"
max_batch_size: 1
input [
  {
    name: "image_path"
    data_type: TYPE_STRING
    dims: [ 1 ]
  }
]
output [
  {
    name: "latent_file_path"
    data_type: TYPE_STRING
    dims: [ 1 ]
  }
]
```

Python model file structure:
```
latent_encoder/
├── config.pbtxt
├── 1/
│   └── model.py
└── model.py (wrapper)
```

---

## Triton Client Examples

### Python gRPC Client
```python
import tritonclient.grpc as grpcclient

client = grpcclient.InferenceServerClient(url='localhost:8001')

inputs = []
inputs.append(grpcclient.InferInput('input_image', [1, 3, 1024, 1024], 'FP32'))
inputs[0].set_data_from_numpy(image_array)

outputs = []
outputs.append(grpcclient.InferRequestedOutput('latent'))

result = client.infer('latent_encoder', inputs, outputs=outputs)
latent = result.as_numpy('latent')
```

---

## Model Conversion Pipeline

1. **Export from ComfyUI** → PyTorch model
2. **Convert to ONNX**: `torch.onnx.export()`
3. **Optimize ONNX**: `onnxruntime.optimize_model()`
4. **Convert to TensorRT** (optional): `trtexec`
5. **Deploy to Triton**: Copy to model repository

---

## Performance Considerations

- **Batch Processing**: Enable dynamic batching for throughput
- **Model Instances**: Multiple instances for parallel processing
- **GPU Memory**: Allocate sufficient GPU memory per instance
- **Queue Size**: Configure max_queue_delay for latency vs throughput tradeoff

