# Sampling Microservice

## Purpose
Performs diffusion sampling using text encodings and latent image to generate new latent representation.

## Inputs
- **positive_encoding_file** (str): Path to positive text encoding tensor file
- **negative_encoding_file** (str): Path to negative text encoding tensor file
- **latent_file** (str): Path to input latent tensor file
- **unet_model_name** (str, optional): Name of UNET model (default: "qwen_image_edit_2509_fp8_e4m3fn.safetensors")
- **lora_model_name** (str, optional): Name of LoRA model (default: "Qwen-Image-Lightning-4steps-V2.0.safetensors")
- **lora_strength** (float, optional): LoRA strength (default: 1.0)
- **sampling_params** (dict, optional): Sampling parameters:
  - seed (int): Random seed (default: random)
  - steps (int): Number of steps (default: 4)
  - cfg (float): CFG scale (default: 1.0)
  - sampler_name (str): Sampler name (default: "euler")
  - scheduler (str): Scheduler name (default: "simple")
  - denoise (float): Denoise strength (default: 1.0)
- **model_transform_params** (dict, optional): Model transformation parameters:
  - shift (int): AuraFlow shift (default: 3)
  - strength (float): CFG normalization strength (default: 1.0)

## Outputs
- **sampled_latent_file** (str): Path to sampled latent tensor file
- **sampled_latent_shape** (tuple): Shape of sampled latent
- **sampling_metadata** (dict): Metadata about sampling process

## Output Format
- Sampled latent saved as: `{output_dir}/sampled_latent_{timestamp}_{hash}.pt`
- JSON metadata file with sampling parameters and metadata

## Dependencies
- ComfyUI nodes: UNETLoader, LoraLoaderModelOnly, ModelSamplingAuraFlow, CFGNorm, KSampler
- Python packages: torch, numpy

## Error Handling
- Returns error if input files not found
- Returns error if models not found
- Returns error if sampling fails

## Example Usage
```python
from sampling import sample_latent

result = sample_latent(
    positive_encoding_file="/path/to/positive_encoding.pt",
    negative_encoding_file="/path/to/negative_encoding.pt",
    latent_file="/path/to/input_latent.pt",
    sampling_params={
        "seed": 12345,
        "steps": 4,
        "cfg": 1.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 1.0
    },
    output_dir="/path/to/output"
)

print(f"Sampled latent: {result['sampled_latent_file']}")
```

