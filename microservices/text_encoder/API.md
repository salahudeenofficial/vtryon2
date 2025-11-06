# Text Encoder Microservice

## Purpose
Encodes text prompts and images into conditioning tensors for diffusion sampling.

## Inputs
- **image1_path** (str): Path to the first image (masked person - needs scaling)
- **image2_path** (str): Path to the second image (cloth image)
- **prompt** (str): Text prompt for positive conditioning
- **negative_prompt** (str, optional): Text prompt for negative conditioning (default: "")
- **clip_model_name** (str, optional): Name of CLIP model (default: "qwen_2.5_vl_7b_fp8_scaled.safetensors")
- **vae_model_name** (str, optional): Name of VAE model (default: "qwen_image_vae.safetensors")
- **upscale_method** (str, optional): Method for image1 scaling (default: "lanczos")
- **megapixels** (float, optional): Target megapixels for scaling (default: 1.0)

## Outputs
- **positive_encoding_file** (str): Path to positive text encoding tensor
- **negative_encoding_file** (str): Path to negative text encoding tensor
- **positive_encoding_shape** (tuple): Shape of positive encoding
- **negative_encoding_shape** (tuple): Shape of negative encoding

## Output Format
- Positive encoding saved as: `{output_dir}/positive_encoding_{timestamp}_{hash}.pt`
- Negative encoding saved as: `{output_dir}/negative_encoding_{timestamp}_{hash}.pt`
- JSON metadata file with encoding shapes and metadata

## Dependencies
- ComfyUI nodes: CLIPLoader, VAELoader, LoadImage, ImageScaleToTotalPixels, TextEncodeQwenImageEditPlus
- Python packages: torch, PIL, numpy

## Error Handling
- Returns error if image files not found
- Returns error if CLIP/VAE models not found
- Returns error if encoding fails

## Example Usage
```python
from text_encoder import encode_text_and_images

result = encode_text_and_images(
    image1_path="/path/to/masked_person.jpg",
    image2_path="/path/to/cloth.png",
    prompt="by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.",
    negative_prompt="",
    output_dir="/path/to/output"
)

print(f"Positive encoding: {result['positive_encoding_file']}")
print(f"Negative encoding: {result['negative_encoding_file']}")
```

