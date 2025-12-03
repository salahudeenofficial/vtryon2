# Files Copied to gpu-server-qwen

## Core Python Files
- `model_cache.py` - Model caching system
- `workflow_script_serial.py` - Workflow execution
- `main.py` - ComfyUI entry point
- `nodes.py` - Node definitions
- `execution.py` - Execution engine
- `folder_paths.py` - Model path management
- `node_helpers.py` - Node helper functions
- `latent_preview.py` - Latent preview utilities
- `protocol.py` - Protocol definitions
- `cuda_malloc.py` - CUDA memory management
- `comfyui_version.py` - Version info

## Core Directories
- `comfy/` - ComfyUI core library (full directory)
- `comfy_execution/` - Execution utilities
- `comfy_api/` - API definitions
- `comfy_config/` - Configuration parser
- `comfy_extras/` - Extra ComfyUI modules
- `app/` - Application management (model_manager, user_manager, etc.)
- `custom_nodes/` - Custom node implementations
- `utils/` - Utility functions
- `middleware/` - Middleware components

## Setup Files
- `setup.sh` - Setup script
- `download.sh` - Model download script
- `requirements.txt` - Python dependencies
- `extra_model_paths.yaml.example` - Model paths config example
- `pyproject.toml` - Project configuration

## New Structure (To Be Created)
- `app/routers/` - API endpoint routers (empty, to be created)
- `app/service/` - Business logic services (empty, to be created)
- `models/` - Request/response models (empty, to be created)
- `configs/` - Configuration files (empty, to be created)

## Total Size
~69MB (includes all ComfyUI core and custom nodes)

## Self-Contained
✅ All dependencies are within this folder
✅ No external file dependencies
✅ Ready for Docker containerization

