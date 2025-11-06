# Latent Encoder Service - Implementation Structure

## File Structure

```
latent_encoder/
├── API.md                    # API documentation
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container build
├── README.md                 # Service README
├── .env.example              # Environment variables template
├── main.py                   # Entry point (mode selector)
├── service.py                # Core service logic
├── kafka_handler.py         # Kafka consumer/producer
├── rest_api.py              # REST API endpoints
├── config.py                # Configuration management
├── models.py                # Data models (Pydantic)
├── errors.py                # Custom exceptions
├── utils.py                 # Utility functions
└── tests/
    ├── __init__.py
    ├── test_service.py      # Unit tests
    ├── test_kafka.py        # Kafka tests
    ├── test_rest_api.py     # REST API tests
    └── fixtures/
        └── test_images/     # Test images
```

---

## Implementation Steps

### Step 1: Setup Project Structure ✅
- [x] Create directory structure
- [x] Create requirements.txt
- [x] Create API.md documentation

### Step 2: Create Core Files
- [ ] Create `config.py` - Configuration management
- [ ] Create `errors.py` - Custom exceptions
- [ ] Create `models.py` - Pydantic models
- [ ] Create `utils.py` - Utility functions

### Step 3: Extract Core Logic
- [ ] Create `service.py` - Extract encoding logic from workflow_script_serial.py
- [ ] Implement `encode_image_to_latent()` function
- [ ] Add error handling
- [ ] Add input validation

### Step 4: Add Kafka Integration
- [ ] Create `kafka_handler.py`
- [ ] Implement Kafka consumer
- [ ] Implement Kafka producer
- [ ] Add message serialization/deserialization
- [ ] Add error handling and DLQ

### Step 5: Add REST API
- [ ] Create `rest_api.py` with FastAPI
- [ ] Add `/api/v1/latent/encode` endpoint
- [ ] Add `/health` endpoint
- [ ] Add request validation

### Step 6: Create Main Entry Point
- [ ] Create `main.py`
- [ ] Add mode selection (kafka/rest/standalone)
- [ ] Add CLI argument parsing
- [ ] Initialize service based on mode

### Step 7: Add Testing
- [ ] Create `tests/test_service.py`
- [ ] Create `tests/test_kafka.py`
- [ ] Create `tests/test_rest_api.py`
- [ ] Add test fixtures

### Step 8: Add Logging & Monitoring
- [ ] Add structured logging
- [ ] Add request ID tracking
- [ ] Add performance metrics

---

## Next Steps Checklist

1. **Create core service logic** (`service.py`)
   - Extract encoding pipeline from workflow_script_serial.py
   - Wrap in try/except with proper error handling
   - Return structured response

2. **Setup configuration** (`config.py`)
   - Environment variable loading
   - Default values
   - Validation

3. **Setup Kafka** (`kafka_handler.py`)
   - Consumer for requests
   - Producer for responses
   - Error handling

4. **Setup REST API** (`rest_api.py`)
   - FastAPI app
   - Endpoints
   - Request/response models

5. **Create main entry** (`main.py`)
   - Mode selection
   - Service initialization
   - CLI arguments

6. **Add tests**
   - Unit tests for core logic
   - Integration tests with Kafka
   - API tests

7. **Test individually**
   - Standalone mode for development
   - REST API for manual testing
   - Kafka mode for integration testing

---

## Testing Commands

### Standalone Testing
```bash
python main.py --mode standalone \
  --image_path test_set/male/masked_person/1.jpg \
  --output_dir ./output
```

### REST API Testing
```bash
python main.py --mode rest --port 8080

# Test endpoint
curl -X POST http://localhost:8080/api/v1/latent/encode \
  -H "Content-Type: application/json" \
  -d '{"image_path": "test.jpg"}'
```

### Kafka Testing
```bash
# Start Kafka (if not running)
docker-compose up -d kafka

# Run service
python main.py --mode kafka

# Send test message
python scripts/send_test_message.py
```

---

## Implementation Priority

1. **First**: Core service logic (`service.py`) - Extract and test
2. **Second**: Configuration and error handling
3. **Third**: REST API for easy testing
4. **Fourth**: Kafka integration
5. **Fifth**: Comprehensive testing

