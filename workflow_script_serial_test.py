"""
Test script that dumps expected output tensors for all 4 microservices.

This script runs the full workflow and saves expected output tensors for:
1. latent_encoder - Image to latent encoding
2. text_encoder - Text and image encoding (positive and negative)
3. sampling - Diffusion sampling output
4. decoding - Latent to image decoding

Outputs are saved as PyTorch tensors (.pt files) for comparison.
"""
import os
import random
import sys
import torch
from pathlib import Path
from typing import Sequence, Mapping, Any, Union


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    """Returns the value at the given index of a sequence or mapping."""
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def find_path(name: str, path: str = None) -> str:
    """Recursively looks at parent folders starting from the given path until it finds the given name."""
    if path is None:
        path = os.getcwd()
    
    if name in os.listdir(path):
        path_name = os.path.join(path, name)
        print(f"{name} found: {path_name}")
        return path_name
    
    parent_directory = os.path.dirname(path)
    
    if parent_directory == path:
        return None
    
    return find_path(name, parent_directory)


def add_comfyui_directory_to_sys_path() -> None:
    """Add 'ComfyUI' to the sys.path"""
    comfyui_path = find_path("ComfyUI")
    if comfyui_path is not None and os.path.isdir(comfyui_path):
        sys.path.append(comfyui_path)
        print(f"'{comfyui_path}' added to sys.path")


def add_extra_model_paths() -> None:
    """Parse the optional extra_model_paths.yaml file and add the parsed paths to the sys.path."""
    try:
        from main import load_extra_path_config
    except ImportError:
        print("Could not import load_extra_path_config from main.py. Looking in utils.extra_config instead.")
        from utils.extra_config import load_extra_path_config

    extra_model_paths = find_path("extra_model_paths.yaml")

    if extra_model_paths is not None:
        load_extra_path_config(extra_model_paths)
    else:
        print("Could not find the extra_model_paths config file.")


add_comfyui_directory_to_sys_path()
add_extra_model_paths()


def import_custom_nodes_minimal() -> None:
    """Minimal custom node loading using asyncio.run() without server infrastructure."""
    import asyncio
    from nodes import init_extra_nodes
    
    asyncio.run(init_extra_nodes(init_custom_nodes=True, init_api_nodes=False))


from nodes import (
    UNETLoader,
    CLIPLoader,
    SaveImage,
    VAEEncode,
    LoadImage,
    KSampler,
    VAELoader,
    NODE_CLASS_MAPPINGS,
    VAEDecode,
    LoraLoaderModelOnly,
)


def save_tensor(tensor, filepath: str, description: str):
    """Save tensor to file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    # Handle case where tensor might be wrapped in a dict or list
    if isinstance(tensor, dict):
        # Try to extract tensor from dict
        if "samples" in tensor:
            tensor = tensor["samples"]
        elif "latent" in tensor:
            tensor = tensor["latent"]
        elif "result" in tensor:
            tensor = tensor["result"][0] if isinstance(tensor["result"], (list, tuple)) else tensor["result"]
        elif len(tensor) == 1:
            # If dict has single key, use its value
            tensor = list(tensor.values())[0]
        else:
            raise ValueError(f"Cannot extract tensor from dict: {list(tensor.keys())}")
    
    if isinstance(tensor, (list, tuple)):
        tensor = tensor[0]
    
    # Ensure it's a tensor
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"Expected torch.Tensor, got {type(tensor)}")
    
    torch.save(tensor, filepath)
    print(f"✓ Saved {description}: {filepath}")
    print(f"  Shape: {tensor.shape}")
    print(f"  Dtype: {tensor.dtype}")


def main():
    """Main workflow function - saves expected output tensors for all 4 APIs."""
    
    # Output directory for test tensors
    output_dir = Path("./test_outputs")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Expected Output Tensors for All 4 Microservices")
    print("=" * 60)
    
    # Load custom nodes
    import_custom_nodes_minimal()
    
    with torch.inference_mode():
        print("\n[1/4] Loading models...")
        unetloader = UNETLoader()
        unetloader_37 = unetloader.load_unet(
            unet_name="qwen_image_edit_2509_fp8_e4m3fn.safetensors",
            weight_dtype="default",
        )

        cliploader = CLIPLoader()
        cliploader_38 = cliploader.load_clip(
            clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors",
            type="qwen_image",
            device="default",
        )

        vaeloader = VAELoader()
        vaeloader_39 = vaeloader.load_vae(vae_name="qwen_image_vae.safetensors")

        loadimage = LoadImage()
        loadimage_78 = loadimage.load_image(image="masked_person.png")

        imagescaletototalpixels = NODE_CLASS_MAPPINGS["ImageScaleToTotalPixels"]()
        imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(
            upscale_method="lanczos",
            megapixels=1,
            image=get_value_at_index(loadimage_78, 0),
        )

        print("\n[2/4] Latent Encoder - Encoding image to latent...")
        vaeencode = VAEEncode()
        vaeencode_88 = vaeencode.encode(
            pixels=get_value_at_index(imagescaletototalpixels_93, 0),
            vae=get_value_at_index(vaeloader_39, 0),
        )
        img1_enc = get_value_at_index(vaeencode_88, 0)
        
        # Debug: Check what type img1_enc is
        if isinstance(img1_enc, dict):
            print(f"  Debug: img1_enc is dict with keys: {list(img1_enc.keys())}")
            # Try to extract the actual tensor
            if "samples" in img1_enc:
                img1_enc = img1_enc["samples"]
            elif "latent" in img1_enc:
                img1_enc = img1_enc["latent"]
            elif len(img1_enc) == 1:
                img1_enc = list(img1_enc.values())[0]
        
        # Save latent encoder output
        save_tensor(
            img1_enc,
            str(output_dir / "latent_encoder_output.pt"),
            "Latent Encoder Output"
        )

        loraloadermodelonly = LoraLoaderModelOnly()
        loraloadermodelonly_89 = loraloadermodelonly.load_lora_model_only(
            lora_name="Qwen-Image-Lightning-4steps-V2.0.safetensors",
            strength_model=1,
            model=get_value_at_index(unetloader_37, 0),
        )

        loadimage_106 = loadimage.load_image(image="cloth.png")

        print("\n[3/4] Text Encoder - Encoding prompts...")
        textencodeqwenimageeditplus = NODE_CLASS_MAPPINGS[
            "TextEncodeQwenImageEditPlus"
        ]()
        
        textencodeqwenimageeditplus_111 = textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
            prompt="by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.",
            clip=get_value_at_index(cliploader_38, 0),
            vae=get_value_at_index(vaeloader_39, 0),
            image1=get_value_at_index(imagescaletototalpixels_93, 0),
            image2=get_value_at_index(loadimage_106, 0),
        )

        textencodeqwenimageeditplus_110 = (
            textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
                prompt="",
                clip=get_value_at_index(cliploader_38, 0),
                vae=get_value_at_index(vaeloader_39, 0),
                image1=get_value_at_index(imagescaletototalpixels_93, 0),
                image2=get_value_at_index(loadimage_106, 0),
            )
        )
        
        t_en_out1 = get_value_at_index(textencodeqwenimageeditplus_111, 0)
        t_en_out2 = get_value_at_index(textencodeqwenimageeditplus_110, 0)
        
        # Handle dict outputs from text encoder
        if isinstance(t_en_out1, dict):
            if "cond" in t_en_out1:
                t_en_out1 = t_en_out1["cond"]
            elif len(t_en_out1) == 1:
                t_en_out1 = list(t_en_out1.values())[0]
        
        if isinstance(t_en_out2, dict):
            if "cond" in t_en_out2:
                t_en_out2 = t_en_out2["cond"]
            elif len(t_en_out2) == 1:
                t_en_out2 = list(t_en_out2.values())[0]
        
        # Save text encoder outputs
        save_tensor(
            t_en_out1,
            str(output_dir / "text_encoder_positive_output.pt"),
            "Text Encoder Positive Output"
        )
        save_tensor(
            t_en_out2,
            str(output_dir / "text_encoder_negative_output.pt"),
            "Text Encoder Negative Output"
        )

        emptysd3latentimage = NODE_CLASS_MAPPINGS["EmptySD3LatentImage"]()
        emptysd3latentimage_112 = emptysd3latentimage.EXECUTE_NORMALIZED(
            width=1024, height=1024, batch_size=1
        )

        modelsamplingauraflow = NODE_CLASS_MAPPINGS["ModelSamplingAuraFlow"]()
        cfgnorm = NODE_CLASS_MAPPINGS["CFGNorm"]()
        ksampler = KSampler()
        
        print("\n[4/4] Sampling - Running diffusion sampling...")
        modelsamplingauraflow_66 = modelsamplingauraflow.patch_aura(
            shift=3, model=get_value_at_index(loraloadermodelonly_89, 0)
        )

        cfgnorm_75 = cfgnorm.EXECUTE_NORMALIZED(
            strength=1, model=get_value_at_index(modelsamplingauraflow_66, 0)
        )
        
        # Use fixed seed for reproducibility
        test_seed = 12345
        ksampler_3 = ksampler.sample(
            seed=test_seed,
            steps=4,
            cfg=1,
            sampler_name="euler",
            scheduler="simple",
            denoise=1,
            model=get_value_at_index(cfgnorm_75, 0),
            positive=t_en_out1,
            negative=t_en_out2,
            latent_image=img1_enc,
        )
        k_out = get_value_at_index(ksampler_3, 0)
        
        # Handle dict outputs from sampler
        if isinstance(k_out, dict):
            if "samples" in k_out:
                k_out = k_out["samples"]
            elif "latent" in k_out:
                k_out = k_out["latent"]
            elif len(k_out) == 1:
                k_out = list(k_out.values())[0]
        
        # Save sampling output
        save_tensor(
            k_out,
            str(output_dir / "sampling_output.pt"),
            "Sampling Output"
        )

        print("\n[5/4] Decoding - Decoding latent to image...")
        vaedecode = VAEDecode()
        vaedecode_8 = vaedecode.decode(
            samples=k_out,
            vae=get_value_at_index(vaeloader_39, 0),
        )
        decoded_image = get_value_at_index(vaedecode_8, 0)
        
        # Handle dict outputs from decoder
        if isinstance(decoded_image, dict):
            if "image" in decoded_image:
                decoded_image = decoded_image["image"]
            elif "pixels" in decoded_image:
                decoded_image = decoded_image["pixels"]
            elif len(decoded_image) == 1:
                decoded_image = list(decoded_image.values())[0]
        
        # Save decoding output (image tensor)
        save_tensor(
            decoded_image,
            str(output_dir / "decoding_output.pt"),
            "Decoding Output"
        )
        
        print("\n" + "=" * 60)
        print("✓ All expected output tensors generated successfully!")
        print(f"Output directory: {output_dir.absolute()}")
        print("\nGenerated files:")
        print("  - latent_encoder_output.pt")
        print("  - text_encoder_positive_output.pt")
        print("  - text_encoder_negative_output.pt")
        print("  - sampling_output.pt")
        print("  - decoding_output.pt")
        print("=" * 60)


if __name__ == "__main__":
    main()

