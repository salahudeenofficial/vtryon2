# Latent Encoder Microservice

## Quick Start

### 1. Setup (Clone modules and download models)
```bash
bash setup.sh
```

### 2. Install Dependencies
```bash
pip install -r ../../requirements.txt  # ComfyUI base
pip install -r requirements.txt        # Additional packages
```

### 3. Test Standalone Mode
```bash
python main.py --mode standalone --image_path input/masked_person.png

# To get tensor output without saving:
python main.py --mode standalone --image_path input/masked_person.png --no-save
```

### 4. Test Kafka Mode
```bash
python main.py --mode kafka
```

## Service Modes

- **standalone**: Direct execution for testing
- **kafka**: Kafka consumer/producer

## Input/Output

See `API.md` for complete API documentation.

