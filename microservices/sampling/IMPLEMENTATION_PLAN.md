# Sampling Microservice - Implementation Plan

## Overview
The sampling microservice performs diffusion sampling using text encodings and latent image to generate a new latent representation. It requires UNET model, LoRA model, and applies model transformations before sampling.

## Implementation Steps

### Step 1: Create Core Service Files
Based on `latent_encoder` and `text_encoder` structure, create:

1. **`config.py`** - Configuration management
   - Load environment variables
   - Define model paths (UNET, LoRA)
   - Define default sampling parameters
   - Define default model transformation parameters

2. **`errors.py`** - Custom exceptions
   - `UNETModelNotFoundError`
   - `LoRAModelNotFoundError`
   - `SamplingFailedError`
   - `InputTensorNotFoundError`
   - `OutputDirNotWritableError`
   - `ComfyUIInitializationError`

3. **`models.py`** - Pydantic data models
   - `SamplingRequest` (for standalone mode)
   - `SamplingResponse`
   - `KafkaSamplingRequest` (for Kafka mode)
   - `KafkaSamplingResponse`

4. **`utils.py`** - Utility functions
   - Copy from `latent_encoder/utils.py` (same utilities needed)
   - `get_value_at_index`
   - `add_comfyui_directory_to_sys_path`
   - `add_extra_model_paths`
   - `generate_request_id`
   - `ensure_directory_exists`
   - `load_tensor_from_file` (new - load tensors from .pt files)

5. **`service.py`** - Core sampling logic
   - `setup_comfyui()` - Initialize ComfyUI paths and models
   - `sample_latent()` - Main sampling function
     - Load UNET model
     - Load LoRA model and apply to UNET
     - Apply ModelSamplingAuraFlow (patch_aura)
     - Apply CFGNorm
     - Load input tensors (positive, negative, latent)
     - Run KSampler
     - Extract and return sampled latent tensor

6. **`kafka_handler.py`** - Kafka consumer/producer
   - Consumer for sampling requests
   - Producer for sampling responses
   - Message serialization/deserialization

7. **`main.py`** - Entry point
   - CLI argument parsing
   - Mode selection (standalone/kafka)
   - Service initialization

### Step 2: Create Setup Scripts

1. **`setup.sh`** - Comprehensive setup script
   - Create Python 3.13 virtual environment
   - Install PyTorch with CUDA 13.0
   - Clone ComfyUI files from master branch
   - Clone requirements.txt and append additional dependencies
   - Install all dependencies
   - Download required models (UNET and LoRA)

2. **`.env.example`** - Environment variable template
   - Kafka configuration
   - Model paths
   - Output directory
   - Default sampling parameters

### Step 3: Update Documentation

1. **`README.md`** - Quick start guide
   - Setup instructions
   - Usage examples (standalone and Kafka)
   - Testing instructions

2. **`API.md`** - Update with implementation details
   - Input/output specifications
   - Error handling
   - Examples

### Step 4: Key Implementation Details

#### Service Function Signature
```python
def sample_latent(
    positive_encoding: Union[str, torch.Tensor],  # Path to .pt file or tensor
    negative_encoding: Union[str, torch.Tensor],  # Path to .pt file or tensor
    latent_image: Union[str, torch.Tensor],  # Path to .pt file or tensor
    unet_model_name: str = None,  # Default from config
    lora_model_name: str = None,  # Default from config
    lora_strength: float = 1.0,
    seed: int = None,  # Random if not provided
    steps: int = 4,
    cfg: float = 1.0,
    sampler_name: str = "euler",
    scheduler: str = "simple",
    denoise: float = 1.0,
    shift: int = 3,  # AuraFlow shift
    strength: float = 1.0,  # CFGNorm strength
    output_dir: str = None,
    request_id: str = None,
    save_tensor: bool = True
) -> dict
```

#### ComfyUI Nodes Required
1. **UNETLoader** - Load UNET model
2. **LoraLoaderModelOnly** - Load and apply LoRA to UNET
3. **ModelSamplingAuraFlow** - Apply AuraFlow transformation
4. **CFGNorm** - Apply CFG normalization
5. **KSampler** - Perform diffusion sampling

#### Input Format Handling
- Accept tensor files (.pt) OR tensor objects directly
- Positive/negative encodings: Can be list/tuple format `[tensor, metadata]` or just tensor
- Latent image: Must be dict format `{"samples": tensor}` for sampler

#### Output Format
- Returns dict with:
  - `sampled_latent_tensor`: torch.Tensor (or path if saved)
  - `sampled_latent_shape`: tuple
  - `metadata`: dict with processing info
- Sampled latent is in dict format `{"samples": tensor}` for passing to decoder

### Step 5: Model Dependencies

#### Required Models
1. **UNET Model**: `qwen_image_edit_2509_fp8_e4m3fn.safetensors` or `qwen_image_edit_fp8_e4m3fn.safetensors`
   - Location: `models/diffusion_models/`
   - Download in `setup.sh`

2. **LoRA Model**: `Qwen-Image-Lightning-4steps-V2.0.safetensors`
   - Location: `models/loras/`
   - Download in `setup.sh`

### Step 6: Input Tensor Loading

The service needs to handle loading tensors from files or accepting them directly:
- If string path provided: Load from .pt file
- If tensor provided: Use directly
- Handle different formats:
  - Conditioning: `[tensor, metadata_dict]` or just `tensor`
  - Latent: `{"samples": tensor}` or just `tensor` (wrap if needed)

### Step 7: Testing

1. **Standalone Test**
   ```bash
   python main.py --mode standalone \
     --positive_encoding test_outputs/text_encoder_positive_output.pt \
     --negative_encoding test_outputs/text_encoder_negative_output.pt \
     --latent_image test_outputs/latent_encoder_output.pt \
     --seed 12345
   ```

2. **Tensor Comparison Test**
   - Create `test_step3.py` in parent directory
   - Compare `sampling_output.pt` from `workflow_script_serial_test.py`
   - With actual service output

### Step 8: File Structure
```
sampling/
├── config.py
├── errors.py
├── models.py
├── utils.py
├── service.py
├── kafka_handler.py
├── main.py
├── setup.sh
├── .env.example
├── README.md
├── API.md
├── Dockerfile
├── requirements.txt
├── comfyui/          # Cloned from master branch
├── models/           # Downloaded models
│   ├── diffusion_models/
│   └── loras/
└── venv/             # Virtual environment
```

## Implementation Order

1. ✅ Copy `utils.py` from `latent_encoder` (add `load_tensor_from_file`)
2. ✅ Create `config.py` (add UNET and LoRA model paths, sampling params)
3. ✅ Create `errors.py` (add UNETModelNotFoundError, LoRAModelNotFoundError)
4. ✅ Create `models.py` (SamplingRequest/Response)
5. ✅ Create `service.py` (main sampling logic)
6. ✅ Create `kafka_handler.py` (Kafka integration)
7. ✅ Create `main.py` (entry point)
8. ✅ Create `setup.sh` (setup script with UNET+LoRA download)
9. ✅ Create `.env.example`
10. ✅ Update `README.md`
11. ✅ Test standalone mode
12. ✅ Create `test_step3.py` for tensor comparison

## Key Differences from Previous Microservices

1. **Multiple Model Dependencies**: Needs UNET + LoRA (not just one model)
2. **Model Transformations**: Applies AuraFlow and CFGNorm before sampling
3. **Multiple Input Tensors**: Takes 3 inputs (positive, negative, latent)
4. **Input Format Flexibility**: Accepts file paths OR tensor objects
5. **Sampling Parameters**: Many configurable parameters (seed, steps, cfg, etc.)
6. **Output Format**: Returns dict format `{"samples": tensor}` for decoder compatibility

## Next Steps

1. Start with Step 1: Create core service files
2. Test with standalone mode using outputs from previous microservices
3. Verify tensor extraction matches `workflow_script_serial_test.py` output
4. Implement Kafka handler
5. Create test comparison script



