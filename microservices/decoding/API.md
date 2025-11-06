# Decoding Microservice

## Purpose
Decodes latent tensors back to image files.

## Inputs
- **latent_file** (str): Path to latent tensor file
- **vae_model_name** (str, optional): Name of VAE model (default: "qwen_image_vae.safetensors")
- **output_filename** (str, optional): Base name for output file (default: "output")
- **output_dir** (str, optional): Directory to save output (default: "./output")
- **output_format** (str, optional): Output image format - "jpg", "png", "webp" (default: "jpg")

## Outputs
- **image_file_path** (str): Path to the decoded image file
- **image_shape** (tuple): Shape of the decoded image (height, width, channels)
- **file_size** (int): Size of the output file in bytes

## Output Format
- Image saved as: `{output_dir}/{output_filename}_{timestamp}.{format}`
- JSON metadata file with image metadata

## Dependencies
- ComfyUI nodes: VAELoader, VAEDecode, SaveImage
- Python packages: torch, PIL, numpy

## Error Handling
- Returns error if latent file not found
- Returns error if VAE model not found
- Returns error if decoding fails
- Returns error if output directory is not writable

## Example Usage
```python
from decoding import decode_latent_to_image

result = decode_latent_to_image(
    latent_file="/path/to/sampled_latent.pt",
    output_filename="test_male_1",
    output_dir="/path/to/output",
    output_format="jpg"
)

print(f"Image saved at: {result['image_file_path']}")
print(f"Image shape: {result['image_shape']}")
```

