# Latent Encoder Service - Core Implementation

This file contains the core encoding logic extracted from the workflow.

## Function Signature

```python
def encode_image_to_latent(
    image_path: str,
    vae_model_name: str = "qwen_image_vae.safetensors",
    output_dir: str = "./output",
    upscale_method: str = "lanczos",
    megapixels: float = 1.0,
    model_dir: str = None,
    comfyui_path: str = None
) -> dict:
    """
    Encode image to latent space representation.
    
    Args:
        image_path: Path to input image
        vae_model_name: Name of VAE model file
        output_dir: Directory to save outputs
        upscale_method: Image scaling method
        megapixels: Target megapixels for scaling
        model_dir: Directory containing models
        comfyui_path: Path to ComfyUI installation
        
    Returns:
        dict: {
            "status": "success" | "error",
            "request_id": str,
            "latent_file_path": str,
            "latent_shape": list,
            "error_message": str | None,
            "metadata": dict
        }
    """
    pass
```

## Implementation Notes

1. Extract code from `workflow_script_serial.py` lines 229-243
2. Wrap in error handling
3. Add input validation
4. Save outputs to specified directory
5. Return structured response

