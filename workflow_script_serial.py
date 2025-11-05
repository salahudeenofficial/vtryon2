import os
import random
import sys
from typing import Sequence, Mapping, Any, Union
import torch
import glob
from pathlib import Path


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    """Returns the value at the given index of a sequence or mapping.

    If the object is a sequence (like list or string), returns the value at the given index.
    If the object is a mapping (like a dictionary), returns the value at the index-th key.

    Some return a dictionary, in these cases, we look for the "results" key

    Args:
        obj (Union[Sequence, Mapping]): The object to retrieve the value from.
        index (int): The index of the value to retrieve.

    Returns:
        Any: The value at the given index.

    Raises:
        IndexError: If the index is out of bounds for the object and the object is not a mapping.
    """
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]


def find_path(name: str, path: str = None) -> str:
    """
    Recursively looks at parent folders starting from the given path until it finds the given name.
    Returns the path as a Path object if found, or None otherwise.
    """
    # If no path is given, use the current working directory
    if path is None:
        path = os.getcwd()

    # Check if the current directory contains the name
    if name in os.listdir(path):
        path_name = os.path.join(path, name)
        print(f"{name} found: {path_name}")
        return path_name

    # Get the parent directory
    parent_directory = os.path.dirname(path)

    # If the parent directory is the same as the current directory, we've reached the root and stop the search
    if parent_directory == path:
        return None

    # Recursively call the function with the parent directory
    return find_path(name, parent_directory)


def add_comfyui_directory_to_sys_path() -> None:
    """
    Add 'ComfyUI' to the sys.path
    """
    comfyui_path = find_path("ComfyUI")
    if comfyui_path is not None and os.path.isdir(comfyui_path):
        sys.path.append(comfyui_path)
        print(f"'{comfyui_path}' added to sys.path")


def add_extra_model_paths() -> None:
    """
    Parse the optional extra_model_paths.yaml file and add the parsed paths to the sys.path.
    """
    try:
        from main import load_extra_path_config
    except ImportError:
        print(
            "Could not import load_extra_path_config from main.py. Looking in utils.extra_config instead."
        )
        from utils.extra_config import load_extra_path_config

    extra_model_paths = find_path("extra_model_paths.yaml")

    if extra_model_paths is not None:
        load_extra_path_config(extra_model_paths)
    else:
        print("Could not find the extra_model_paths config file.")


add_comfyui_directory_to_sys_path()
add_extra_model_paths()


def import_custom_nodes_minimal() -> None:
    """
    Minimal custom node loading using asyncio.run() without server infrastructure.
    This is lighter than the full server setup but still requires async execution.
    """
    import asyncio
    from nodes import init_extra_nodes
    
    # Simply run the async function with asyncio.run() - no server needed
    # This creates a new event loop, runs the coroutine, and closes the loop
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


def get_image_pairs(test_set_path: str, gender: str):
    """
    Get matching image pairs from cloth and masked_person folders.
    Returns list of tuples: (cloth_path, masked_person_path, number)
    """
    cloth_dir = os.path.join(test_set_path, gender, "cloth")
    masked_person_dir = os.path.join(test_set_path, gender, "masked_person")
    
    pairs = []
    
    # Get all cloth images
    cloth_files = {}
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        for cloth_path in glob.glob(os.path.join(cloth_dir, ext)):
            base_name = os.path.splitext(os.path.basename(cloth_path))[0]
            cloth_files[base_name] = cloth_path
    
    # Match with masked_person images
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        for masked_path in glob.glob(os.path.join(masked_person_dir, ext)):
            base_name = os.path.splitext(os.path.basename(masked_path))[0]
            if base_name in cloth_files:
                pairs.append((cloth_files[base_name], masked_path, base_name))
    
    # Sort by number
    pairs.sort(key=lambda x: int(x[2]) if x[2].isdigit() else 0)
    
    return pairs


def main():
    """
    Main workflow function - processes test dataset images.
    Processes male first, then female, generating 32 total outputs.
    """
    # Load custom nodes with minimal async setup (no server needed)
    import_custom_nodes_minimal()
    
    # Test dataset path - expects test_set folder next to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_set_path = os.path.join(script_dir, "test_set")
    
    # Get all image pairs
    male_pairs = get_image_pairs(test_set_path, "male")
    female_pairs = get_image_pairs(test_set_path, "female")
    
    print(f"Found {len(male_pairs)} male pairs and {len(female_pairs)} female pairs")
    print(f"Total: {len(male_pairs) + len(female_pairs)} pairs to process")
    
    # Combine: male first, then female
    all_pairs = []
    for cloth_path, masked_path, number in male_pairs:
        all_pairs.append(("male", cloth_path, masked_path, number))
    for cloth_path, masked_path, number in female_pairs:
        all_pairs.append(("female", cloth_path, masked_path, number))
    
    print(f"Processing {len(all_pairs)} pairs (target: 32 outputs)")
    
    with torch.inference_mode():
        # Load models once
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
        imagescaletototalpixels = NODE_CLASS_MAPPINGS["ImageScaleToTotalPixels"]()
        vaeencode = VAEEncode()
        
        loraloadermodelonly = LoraLoaderModelOnly()
        loraloadermodelonly_89 = loraloadermodelonly.load_lora_model_only(
            lora_name="Qwen-Image-Lightning-4steps-V2.0.safetensors",
            strength_model=1,
            model=get_value_at_index(unetloader_37, 0),
        )

        modelsamplingauraflow = NODE_CLASS_MAPPINGS["ModelSamplingAuraFlow"]()
        cfgnorm = NODE_CLASS_MAPPINGS["CFGNorm"]()
        textencodeqwenimageeditplus = NODE_CLASS_MAPPINGS[
            "TextEncodeQwenImageEditPlus"
        ]()
        ksampler = KSampler()
        vaedecode = VAEDecode()
        saveimage = SaveImage()

        # Process each pair
        processed_count = 0
        for gender, cloth_path, masked_person_path, number in all_pairs:
            if processed_count >= 32:
                print(f"Reached target of 32 outputs. Stopping.")
                break
                
            print(f"\nProcessing {gender} pair #{number} ({processed_count + 1}/32)")
            print(f"  Cloth: {cloth_path}")
            print(f"  Person: {masked_person_path}")
            
            try:
                # Load masked person image
                loadimage_78 = loadimage.load_image(image=masked_person_path)
                
                # Scale image
                imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(
                    upscale_method="lanczos",
                    megapixels=1,
                    image=get_value_at_index(loadimage_78, 0),
                )
                
                # Encode to latent
                vaeencode_88 = vaeencode.encode(
                    pixels=get_value_at_index(imagescaletototalpixels_93, 0),
                    vae=get_value_at_index(vaeloader_39, 0),
                )
                
                # Load cloth image
                loadimage_106 = loadimage.load_image(image=cloth_path)
                
                # Apply model sampling
                modelsamplingauraflow_66 = modelsamplingauraflow.patch_aura(
                    shift=3, model=get_value_at_index(loraloadermodelonly_89, 0)
                )

                cfgnorm_75 = cfgnorm.EXECUTE_NORMALIZED(
                    strength=1, model=get_value_at_index(modelsamplingauraflow_66, 0)
                )

                # Encode prompts
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

                # Sample
                ksampler_3 = ksampler.sample(
                    seed=random.randint(1, 2**64),
                    steps=4,
                    cfg=1,
                    sampler_name="euler",
                    scheduler="simple",
                    denoise=1,
                    model=get_value_at_index(cfgnorm_75, 0),
                    positive=get_value_at_index(textencodeqwenimageeditplus_111, 0),
                    negative=get_value_at_index(textencodeqwenimageeditplus_110, 0),
                    latent_image=get_value_at_index(vaeencode_88, 0),
                )

                # Decode
                vaedecode_8 = vaedecode.decode(
                    samples=get_value_at_index(ksampler_3, 0),
                    vae=get_value_at_index(vaeloader_39, 0),
                )

                # Save with descriptive filename
                output_filename = f"test_{gender}_{number}"
                saveimage_60 = saveimage.save_images(
                    filename_prefix=output_filename,
                    images=get_value_at_index(vaedecode_8, 0),
                )
                
                processed_count += 1
                print(f"  ✓ Saved: {output_filename}")
                
            except Exception as e:
                print(f"  ✗ Error processing {gender} pair #{number}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n\nCompleted! Processed {processed_count} pairs successfully.")


if __name__ == "__main__":
    main()
