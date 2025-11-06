# Latent Encoder - Next Steps for Implementation

## Current Status ✅

1. ✅ Updated API.md (removed REST API, focus on Kafka + Standalone)
2. ✅ Created requirements.txt (only additional packages)
3. ✅ Created setup_comfyui.sh script to copy ComfyUI files
4. ✅ Created directory structure
5. ✅ Created implementation plan
6. ✅ Created environment template

## First: Setup ComfyUI Modules and Download Models

```bash
cd microservices/latent_encoder
bash setup.sh
```

This will:
- Clone necessary ComfyUI modules from master branch to `comfyui/` directory
- Download required models to `models/` directory

## Implementation Order

### Step 1: Create Core Service Logic (`service.py`)

**Priority: HIGHEST**

Extract and refactor the encoding logic from `workflow_script_serial.py`:

**Source Code Location:**
- Lines 229-243: Image loading, scaling, VAE encoding

**What to Extract:**
```python
# From workflow_script_serial.py
loadimage_78 = loadimage.load_image(image=masked_person_path)
imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(...)
vaeencode_88 = vaeencode.encode(...)
```

**Create Function:**
```python
def encode_image_to_latent(image_path, vae_model_name, ...):
    # 1. Validate inputs
    # 2. Load image
    # 3. Scale image
    # 4. Encode to latent
    # 5. Save output
    # 6. Return result
```

**Testing:**
- Test with standalone mode first
- Verify output tensor shape
- Verify file is saved correctly

---

### Step 2: Create Configuration (`config.py`)

**Priority: HIGH**

Load configuration from environment variables and CLI args:

```python
class Config:
    mode: str  # standalone, rest, kafka
    kafka_bootstrap_servers: str
    model_dir: str
    output_dir: str
    # ... etc
```

**Features:**
- Load from .env file
- Override with CLI args
- Validate required settings
- Set defaults

---

### Step 3: Create Error Handling (`errors.py`)

**Priority: HIGH**

Define custom exceptions:

```python
class LatentEncoderError(Exception):
    pass

class ImageNotFoundError(LatentEncoderError):
    pass

class VAEModelNotFoundError(LatentEncoderError):
    pass

class EncodingFailedError(LatentEncoderError):
    pass
```

---

### Step 4: Create Data Models (`models.py`)

**Priority: MEDIUM**

Pydantic models for request/response:

```python
from pydantic import BaseModel

class EncodeRequest(BaseModel):
    image_path: str
    vae_model_name: str = "qwen_image_vae.safetensors"
    # ...

class EncodeResponse(BaseModel):
    status: str
    request_id: str
    latent_file_path: str
    # ...
```

---

### Step 5: Create Kafka Handler (`kafka_handler.py`)

**Priority: MEDIUM**

```python
from confluent_kafka import Consumer, Producer

def consume_and_process():
    consumer = Consumer({
        'bootstrap.servers': config.kafka_bootstrap_servers,
        'group.id': 'latent-encoder-group',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([config.kafka_request_topic])
    
    while True:
        msg = consumer.poll(1.0)
        if msg:
            # Deserialize message
            # Process request
            # Send response
            consumer.commit()
```

---

### Step 6: Create Main Entry Point (`main.py`)

**Priority: HIGH**

Mode selector and CLI:

```python
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['standalone', 'rest', 'kafka'])
    parser.add_argument('--image_path', help='For standalone mode')
    # ...
    
    args = parser.parse_args()
    
    if args.mode == 'standalone':
        # Direct execution
        result = encode_image_to_latent(args.image_path)
        print(result)
    elif args.mode == 'rest':
        # Start REST API server
        uvicorn.run(rest_api.app, host=config.rest_host, port=config.rest_port)
    elif args.mode == 'kafka':
        # Start Kafka consumer
        kafka_handler.consume_and_process()
```

---

### Step 7: Add Testing

**Priority: MEDIUM**

Create unit tests:
- Test image loading
- Test encoding
- Test error handling
- Test Kafka message handling
- Test REST API endpoints

---

## Quick Start Command

```bash
# 1. Install dependencies
cd microservices/latent_encoder
pip install -r requirements.txt

# 2. Copy .env.example to .env and configure
cp .env.example .env

# 3. Test standalone mode
python main.py --mode standalone --image_path test.jpg

# 4. Test Kafka mode (requires Kafka running)
docker-compose up -d kafka
python main.py --mode kafka
```

---

## File Dependencies

```
main.py
  ├── config.py (loads settings)
  ├── service.py (core logic)
  ├── rest_api.py (if mode=rest)
  └── kafka_handler.py (if mode=kafka)

service.py
  ├── errors.py (exceptions)
  ├── utils.py (helper functions)
  └── shared_utils (ComfyUI utilities)

rest_api.py
  ├── models.py (Pydantic models)
  └── service.py (calls encoding)

kafka_handler.py
  ├── models.py (message models)
  └── service.py (calls encoding)
```

---

## Testing Strategy

### Phase 1: Standalone Testing
- Test core logic without Kafka/REST
- Verify encoding works
- Debug issues quickly

### Phase 2: REST API Testing
- Test HTTP endpoints
- Verify request/response format
- Test error handling

### Phase 3: Kafka Testing
- Test message consumption
- Test message production
- Test error handling and DLQ

### Phase 4: Integration Testing
- Test full workflow
- Test with real images
- Performance testing

---

## Recommended Starting Point

**Start with `service.py`** - Extract the core logic first:

1. Copy encoding code from `workflow_script_serial.py`
2. Wrap in function with proper inputs/outputs
3. Add error handling
4. Test standalone mode
5. Then add REST API for easy testing
6. Finally add Kafka integration

This allows testing at each step without needing all components at once.

