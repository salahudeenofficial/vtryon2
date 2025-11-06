# Shared Utilities Library

This package contains common utilities shared across all microservices.

## Contents
- `get_value_at_index()`: Utility function to extract values from ComfyUI node outputs
- `find_path()`: Utility to find ComfyUI directory
- `add_comfyui_directory_to_sys_path()`: Setup ComfyUI path
- `add_extra_model_paths()`: Load extra model paths
- `import_custom_nodes_minimal()`: Minimal custom node initialization

## Usage
Install as a package:
```bash
cd shared_utils
pip install -e .
```

Import in your microservices:
```python
from shared_utils import get_value_at_index, find_path
```

