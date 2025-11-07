"""Utility functions for sampling service."""
import os
import sys
import torch
from pathlib import Path
from typing import Sequence, Mapping, Any, Union
import uuid


def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    """
    Returns the value at the given index of a sequence or mapping.
    
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


def add_comfyui_directory_to_sys_path(comfyui_path: Path = None) -> None:
    """
    Add ComfyUI directory to sys.path.
    
    Args:
        comfyui_path: Path to ComfyUI directory. If None, tries to find it.
    """
    if comfyui_path is None:
        comfyui_path_str = find_path("ComfyUI")
    else:
        comfyui_path_str = str(comfyui_path)
    
    if comfyui_path_str is not None and os.path.isdir(comfyui_path_str):
        if comfyui_path_str not in sys.path:
            sys.path.insert(0, comfyui_path_str)
            print(f"'{comfyui_path_str}' added to sys.path")


def add_extra_model_paths(comfyui_path: Path = None) -> None:
    """
    Parse the optional extra_model_paths.yaml file and add the parsed paths to the sys.path.
    
    Args:
        comfyui_path: Path to ComfyUI directory. If None, tries to find it.
    """
    if comfyui_path is None:
        comfyui_path_str = find_path("ComfyUI")
        if comfyui_path_str:
            comfyui_path = Path(comfyui_path_str)
        else:
            print("Could not find ComfyUI directory.")
            return
    
    sys.path.insert(0, str(comfyui_path))
    
    try:
        from main import load_extra_path_config
    except ImportError:
        try:
            from utils.extra_config import load_extra_path_config
        except ImportError:
            print("Could not import load_extra_path_config. Skipping extra model paths.")
            return
    
    extra_model_paths = find_path("extra_model_paths.yaml", str(comfyui_path))
    
    if extra_model_paths is not None:
        load_extra_path_config(extra_model_paths)
    else:
        print("Could not find the extra_model_paths config file.")


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def ensure_directory_exists(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_tensor_from_file(file_path: Union[str, Path]) -> torch.Tensor:
    """
    Load a tensor from a .pt file.
    
    Args:
        file_path: Path to the tensor file
    
    Returns:
        torch.Tensor: Loaded tensor
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file doesn't contain a tensor
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Tensor file not found: {file_path}")
    
    try:
        tensor = torch.load(file_path_obj, map_location='cpu')
        
        # Handle different formats
        if isinstance(tensor, torch.Tensor):
            return tensor
        elif isinstance(tensor, dict):
            # Try common keys
            for key in ["samples", "latent", "tensor"]:
                if key in tensor and isinstance(tensor[key], torch.Tensor):
                    return tensor[key]
            # If only one value, return it
            if len(tensor) == 1:
                value = list(tensor.values())[0]
                if isinstance(value, torch.Tensor):
                    return value
        elif isinstance(tensor, (list, tuple)):
            # Return first tensor found
            for item in tensor:
                if isinstance(item, torch.Tensor):
                    return item
        
        raise ValueError(f"File does not contain a valid tensor: {file_path}")
    except Exception as e:
        raise ValueError(f"Error loading tensor from {file_path}: {e}")



