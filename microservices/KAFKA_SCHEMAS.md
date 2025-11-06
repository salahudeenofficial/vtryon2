# Kafka Message Schemas

## Topic Structure

### Request Topics
- `latent-encoder-requests`
- `text-encoder-requests`
- `sampling-requests`
- `decoding-requests`

### Response Topics
- `latent-encoder-responses`
- `text-encoder-responses`
- `sampling-responses`
- `decoding-responses`

### Orchestration Topic
- `workflow-orchestrator` - For full pipeline orchestration

---

## Avro Schema Definitions

### 1. Latent Encoder Request
```json
{
  "type": "record",
  "name": "LatentEncoderRequest",
  "namespace": "com.vtryon.microservices",
  "fields": [
    {"name": "request_id", "type": "string"},
    {"name": "correlation_id", "type": ["null", "string"], "default": null},
    {"name": "image_path", "type": "string"},
    {"name": "vae_model_name", "type": "string", "default": "qwen_image_vae.safetensors"},
    {"name": "output_dir", "type": "string"},
    {"name": "upscale_method", "type": "string", "default": "lanczos"},
    {"name": "megapixels", "type": "double", "default": 1.0},
    {"name": "timestamp", "type": "long"}
  ]
}
```

### 2. Latent Encoder Response
```json
{
  "type": "record",
  "name": "LatentEncoderResponse",
  "namespace": "com.vtryon.microservices",
  "fields": [
    {"name": "request_id", "type": "string"},
    {"name": "correlation_id", "type": ["null", "string"], "default": null},
    {"name": "status", "type": {"type": "enum", "name": "Status", "symbols": ["success", "error"]}},
    {"name": "latent_file_path", "type": ["null", "string"]},
    {"name": "latent_shape", "type": {"type": "array", "items": "int"}},
    {"name": "error_message", "type": ["null", "string"], "default": null},
    {"name": "timestamp", "type": "long"}
  ]
}
```

### 3. Text Encoder Request
```json
{
  "type": "record",
  "name": "TextEncoderRequest",
  "namespace": "com.vtryon.microservices",
  "fields": [
    {"name": "request_id", "type": "string"},
    {"name": "correlation_id", "type": ["null", "string"], "default": null},
    {"name": "image1_path", "type": "string"},
    {"name": "image2_path", "type": "string"},
    {"name": "prompt", "type": "string"},
    {"name": "negative_prompt", "type": "string", "default": ""},
    {"name": "clip_model_name", "type": "string", "default": "qwen_2.5_vl_7b_fp8_scaled.safetensors"},
    {"name": "vae_model_name", "type": "string", "default": "qwen_image_vae.safetensors"},
    {"name": "timestamp", "type": "long"}
  ]
}
```

### 4. Sampling Request
```json
{
  "type": "record",
  "name": "SamplingRequest",
  "namespace": "com.vtryon.microservices",
  "fields": [
    {"name": "request_id", "type": "string"},
    {"name": "correlation_id", "type": ["null", "string"], "default": null},
    {"name": "positive_encoding_file", "type": "string"},
    {"name": "negative_encoding_file", "type": "string"},
    {"name": "latent_file", "type": "string"},
    {"name": "unet_model_name", "type": "string"},
    {"name": "lora_model_name", "type": "string"},
    {"name": "sampling_params", "type": {
      "type": "record",
      "name": "SamplingParams",
      "fields": [
        {"name": "seed", "type": ["null", "long"], "default": null},
        {"name": "steps", "type": "int", "default": 4},
        {"name": "cfg", "type": "double", "default": 1.0},
        {"name": "sampler_name", "type": "string", "default": "euler"},
        {"name": "scheduler", "type": "string", "default": "simple"},
        {"name": "denoise", "type": "double", "default": 1.0}
      ]
    }},
    {"name": "model_transform_params", "type": {
      "type": "record",
      "name": "ModelTransformParams",
      "fields": [
        {"name": "shift", "type": "int", "default": 3},
        {"name": "strength", "type": "double", "default": 1.0}
      ]
    }},
    {"name": "timestamp", "type": "long"}
  ]
}
```

### 5. Workflow Orchestration Message
```json
{
  "type": "record",
  "name": "WorkflowRequest",
  "namespace": "com.vtryon.microservices",
  "fields": [
    {"name": "workflow_id", "type": "string"},
    {"name": "image1_path", "type": "string"},
    {"name": "image2_path", "type": "string"},
    {"name": "prompt", "type": "string"},
    {"name": "output_filename", "type": "string"},
    {"name": "output_dir", "type": "string"},
    {"name": "steps", "type": {
      "type": "array",
      "items": {
        "type": "record",
        "name": "WorkflowStep",
        "fields": [
          {"name": "service", "type": {"type": "enum", "name": "ServiceType", "symbols": ["latent_encoder", "text_encoder", "sampling", "decoding"]}},
          {"name": "step_id", "type": "string"},
          {"name": "depends_on", "type": {"type": "array", "items": "string"}},
          {"name": "params", "type": "map", "values": "string"}
        ]
      }
    }},
    {"name": "timestamp", "type": "long"}
  ]
}
```

---

## Kafka Producer/Consumer Pattern

### Producer Example
```python
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

producer = Producer({'bootstrap.servers': 'kafka:9092'})
schema_registry = SchemaRegistryClient({'url': 'http://schema-registry:8081'})

# Serialize message
serializer = AvroSerializer(schema_registry, schema_str)

producer.produce(
    topic='latent-encoder-requests',
    value=serializer(message_dict, schema),
    key=request_id
)
```

### Consumer Example
```python
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'latent-encoder-group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['latent-encoder-requests'])

schema_registry = SchemaRegistryClient({'url': 'http://schema-registry:8081'})
deserializer = AvroDeserializer(schema_registry)

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    
    message = deserializer(msg.value(), schema)
    # Process message
    process_latent_encoding(message)
```

---

## Dead Letter Queue (DLQ)

Failed messages are sent to DLQ topics:
- `latent-encoder-dlq`
- `text-encoder-dlq`
- `sampling-dlq`
- `decoding-dlq`

DLQ messages include:
- Original message
- Error details
- Retry count
- Timestamp

