# Latent Encoder Service - Implementation Guide

## Setup Steps

### 1. Setup ComfyUI Modules and Download Models

```bash
cd microservices/latent_encoder
bash setup.sh
```

This will:
- Clone necessary ComfyUI modules from master branch to `comfyui/` directory
- Download required models to `models/` directory

### 2. Install Dependencies

```bash
# Install ComfyUI base requirements (from parent directory)
pip install -r ../../requirements.txt

# Install additional microservice requirements
pip install -r requirements.txt
```

### 3. Setup Environment

```bash
cp .env.example .env
# Edit .env with your paths
```

### 4. Test Standalone Mode

```bash
python main.py --mode standalone --image_path test.jpg
```

### 5. Test Kafka Mode

```bash
# Start Kafka (if not running)
docker-compose up -d kafka

# Run service
python main.py --mode kafka
```

---

## Implementation Order

### Step 1: Create `service.py` (Core Logic)

Extract encoding logic from `workflow_script_serial.py`:

```python
import sys
import os
from pathlib import Path

# Add comfyui to path
sys.path.insert(0, str(Path(__file__).parent / "comfyui"))

# Import ComfyUI utilities
from workflow_script_serial import (
    get_value_at_index,
    find_path,
    add_comfyui_directory_to_sys_path,
    add_extra_model_paths,
    import_custom_nodes_minimal
)

# Import ComfyUI nodes
from nodes import VAELoader, LoadImage, VAEEncode
from nodes import NODE_CLASS_MAPPINGS  # For custom nodes

def encode_image_to_latent(image_path, vae_model_name, ...):
    # Setup ComfyUI paths
    comfyui_path = Path(__file__).parent / "comfyui"
    sys.path.insert(0, str(comfyui_path))
    
    # Setup extra paths
    add_extra_model_paths()
    
    # Load custom nodes
    import_custom_nodes_minimal()
    
    # Load VAE
    vaeloader = VAELoader()
    vae = vaeloader.load_vae(vae_name=vae_model_name)
    
    # Load image
    loadimage = LoadImage()
    image = loadimage.load_image(image=image_path)
    
    # Scale image
    imagescaletototalpixels = NODE_CLASS_MAPPINGS["ImageScaleToTotalPixels"]()
    scaled_image = imagescaletototalpixels.EXECUTE_NORMALIZED(
        upscale_method=upscale_method,
        megapixels=megapixels,
        image=get_value_at_index(image, 0),
    )
    
    # Encode to latent
    vaeencode = VAEEncode()
    encoded = vaeencode.encode(
        pixels=get_value_at_index(scaled_image, 0),
        vae=get_value_at_index(vae, 0),
    )
    
    latent = get_value_at_index(encoded, 0)
    
    # Save latent
    output_path = save_latent(latent, output_dir)
    
    return {
        "status": "success",
        "latent_file_path": output_path,
        "latent_shape": list(latent.shape),
    }
```

### Step 2: Create `config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    mode = os.getenv("MODE", "standalone")
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_request_topic = os.getenv("KAFKA_REQUEST_TOPIC", "latent-encoder-requests")
    kafka_response_topic = os.getenv("KAFKA_RESPONSE_TOPIC", "latent-encoder-responses")
    model_dir = os.getenv("MODEL_DIR", "/models")
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    comfyui_path = os.getenv("COMFYUI_PATH", None)
```

### Step 3: Create `kafka_handler.py`

```python
from confluent_kafka import Consumer, Producer
from config import Config
from service import encode_image_to_latent
import json

def consume_and_process():
    consumer = Consumer({
        'bootstrap.servers': Config.kafka_bootstrap_servers,
        'group.id': 'latent-encoder-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })
    consumer.subscribe([Config.kafka_request_topic])
    
    producer = Producer({
        'bootstrap.servers': Config.kafka_bootstrap_servers
    })
    
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        
        try:
            # Deserialize message
            request = json.loads(msg.value().decode('utf-8'))
            
            # Process request
            result = encode_image_to_latent(
                image_path=request['image_path'],
                vae_model_name=request.get('vae_model_name', 'qwen_image_vae.safetensors'),
                output_dir=request.get('output_dir', './output'),
                # ... other params
            )
            
            # Send response
            response = {
                "request_id": request.get('request_id'),
                "correlation_id": request.get('correlation_id'),
                "status": result["status"],
                "latent_file_path": result.get("latent_file_path"),
                "latent_shape": result.get("latent_shape"),
            }
            
            producer.produce(
                Config.kafka_response_topic,
                key=request.get('request_id'),
                value=json.dumps(response).encode('utf-8')
            )
            producer.flush()
            
            # Commit offset
            consumer.commit(msg)
            
        except Exception as e:
            print(f"Error processing message: {e}")
            # Send error response
            error_response = {
                "request_id": request.get('request_id'),
                "status": "error",
                "error_message": str(e)
            }
            producer.produce(
                Config.kafka_response_topic,
                key=request.get('request_id'),
                value=json.dumps(error_response).encode('utf-8')
            )
            producer.flush()
```

### Step 4: Create `main.py`

```python
import argparse
from config import Config
from service import encode_image_to_latent
from kafka_handler import consume_and_process

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['standalone', 'kafka'], default=Config.mode)
    parser.add_argument('--image_path', help='For standalone mode')
    parser.add_argument('--vae_model_name', default='qwen_image_vae.safetensors')
    parser.add_argument('--output_dir', default='./output')
    # ... other args
    
    args = parser.parse_args()
    
    if args.mode == 'standalone':
        if not args.image_path:
            print("Error: --image_path required for standalone mode")
            return
        
        result = encode_image_to_latent(
            image_path=args.image_path,
            vae_model_name=args.vae_model_name,
            output_dir=args.output_dir,
        )
        print(f"Success: {result['latent_file_path']}")
        print(f"Shape: {result['latent_shape']}")
        
    elif args.mode == 'kafka':
        print("Starting Kafka consumer...")
        consume_and_process()

if __name__ == "__main__":
    main()
```

---

## Testing

### Standalone Test
```bash
python main.py --mode standalone --image_path test.jpg
```

### Kafka Test
```bash
# Terminal 1: Start service
python main.py --mode kafka

# Terminal 2: Send test message
python -c "
import json
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})
message = {
    'request_id': 'test-123',
    'image_path': 'test.jpg',
    'vae_model_name': 'qwen_image_vae.safetensors'
}
producer.produce('latent-encoder-requests', value=json.dumps(message).encode())
producer.flush()
"
```

