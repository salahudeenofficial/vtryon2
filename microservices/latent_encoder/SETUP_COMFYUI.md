# Copy ComfyUI Files Script

This script copies all necessary ComfyUI files to the microservice directory.

## Usage

```bash
# From the microservice directory
bash setup_comfyui.sh /path/to/ComfyUI
```

## What Gets Copied

### Core ComfyUI Files:
- `comfy/` - Entire directory (core libraries)
- `nodes.py` - Node definitions
- `folder_paths.py` - Path management
- `execution.py` - Execution engine
- `main.py` - Main entry (for load_extra_path_config)
- `utils/` - Utility functions
- `comfy_execution/` - Execution utilities
- `comfy_extras/` - Extra nodes
- `custom_nodes/` - All custom nodes
- `node_helpers.py` - Node helper functions
- `comfyui_version.py` - Version info

### Optional Files:
- `extra_model_paths.yaml.example` - Config template
- `pyproject.toml` - Project metadata

## File Structure After Copy

```
latent_encoder/
├── comfyui/          # Copied ComfyUI files
│   ├── comfy/
│   ├── nodes.py
│   ├── folder_paths.py
│   ├── execution.py
│   ├── main.py
│   ├── utils/
│   ├── comfy_execution/
│   ├── comfy_extras/
│   └── custom_nodes/
└── ... (service files)
```

