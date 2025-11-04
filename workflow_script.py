import os
import random
import sys
from typing import Sequence, Mapping, Any, Union
import torch


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


def import_custom_nodes() -> None:
    """Find all custom nodes in the custom_nodes folder and add those node objects to NODE_CLASS_MAPPINGS

    This function sets up a new asyncio event loop, initializes the PromptServer,
    creates a PromptQueue, and initializes the custom nodes.
    """
    import asyncio
    import execution
    from nodes import init_extra_nodes

    sys.path.insert(0, find_path("ComfyUI"))
    import server

    # Creating a new event loop and setting it as the default loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Creating an instance of PromptServer with the loop
    server_instance = server.PromptServer(loop)
    execution.PromptQueue(server_instance)

    # Initializing custom nodes
    asyncio.run(init_extra_nodes())


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


def main():
    import_custom_nodes()
    with torch.inference_mode():
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
        loadimage_78 = loadimage.load_image(
            image="image_qwen_image_edit_2509_input_image.png"
        )

        imagescaletototalpixels = NODE_CLASS_MAPPINGS["ImageScaleToTotalPixels"]()
        imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(
            upscale_method="lanczos",
            megapixels=1,
            image=get_value_at_index(loadimage_78, 0),
        )

        vaeencode = VAEEncode()
        vaeencode_88 = vaeencode.encode(
            pixels=get_value_at_index(imagescaletototalpixels_93, 0),
            vae=get_value_at_index(vaeloader_39, 0),
        )

        loraloadermodelonly = LoraLoaderModelOnly()
        loraloadermodelonly_89 = loraloadermodelonly.load_lora_model_only(
            lora_name="Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors",
            strength_model=1,
            model=get_value_at_index(unetloader_37, 0),
        )

        loadimage_106 = loadimage.load_image(
            image="image_qwen_image_edit_2509_input_image.png"
        )

        emptysd3latentimage = NODE_CLASS_MAPPINGS["EmptySD3LatentImage"]()
        emptysd3latentimage_112 = emptysd3latentimage.EXECUTE_NORMALIZED(
            width=1024, height=1024, batch_size=1
        )

        modelsamplingauraflow = NODE_CLASS_MAPPINGS["ModelSamplingAuraFlow"]()
        cfgnorm = NODE_CLASS_MAPPINGS["CFGNorm"]()
        textencodeqwenimageeditplus = NODE_CLASS_MAPPINGS[
            "TextEncodeQwenImageEditPlus"
        ]()
        ksampler = KSampler()
        vaedecode = VAEDecode()
        imageconcatmulti = NODE_CLASS_MAPPINGS["ImageConcatMulti"]()
        saveimage = SaveImage()

        for q in range(10):
            modelsamplingauraflow_66 = modelsamplingauraflow.patch_aura(
                shift=3, model=get_value_at_index(loraloadermodelonly_89, 0)
            )

            cfgnorm_75 = cfgnorm.EXECUTE_NORMALIZED(
                strength=1, model=get_value_at_index(modelsamplingauraflow_66, 0)
            )

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

            vaedecode_8 = vaedecode.decode(
                samples=get_value_at_index(ksampler_3, 0),
                vae=get_value_at_index(vaeloader_39, 0),
            )

            imageconcatmulti_389 = imageconcatmulti.combine(
                inputcount=3,
                direction="right",
                match_image_size=False,
                Update_inputs=None,
                image_1=get_value_at_index(loadimage_78, 0),
                image_2=get_value_at_index(loadimage_106, 0),
                image_3=get_value_at_index(vaedecode_8, 0),
            )

            saveimage_60 = saveimage.save_images(
                filename_prefix="ComfyUI",
                images=get_value_at_index(imageconcatmulti_389, 0),
            )


if __name__ == "__main__":
    main()
