#!/bin/bash

# setup_comfyui.sh - Copy ComfyUI files to microservice

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_comfyui_root>"
    echo "Example: $0 /home/fashionx/dev/nihal/ComfyUI"
    exit 1
fi

COMFYUI_ROOT="$1"
MICROSERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DEST="${MICROSERVICE_DIR}/comfyui"

if [ ! -d "$COMFYUI_ROOT" ]; then
    echo "Error: ComfyUI directory not found: $COMFYUI_ROOT"
    exit 1
fi

echo "Copying ComfyUI files from: $COMFYUI_ROOT"
echo "Destination: $COMFYUI_DEST"

# Create destination directory
mkdir -p "$COMFYUI_DEST"

# Copy core directories
echo "Copying core directories..."
cp -r "${COMFYUI_ROOT}/comfy" "${COMFYUI_DEST}/"
cp -r "${COMFYUI_ROOT}/utils" "${COMFYUI_DEST}/"
cp -r "${COMFYUI_ROOT}/comfy_execution" "${COMFYUI_DEST}/"
cp -r "${COMFYUI_ROOT}/comfy_extras" "${COMFYUI_DEST}/"
cp -r "${COMFYUI_ROOT}/custom_nodes" "${COMFYUI_DEST}/"

# Copy core Python files
echo "Copying core Python files..."
cp "${COMFYUI_ROOT}/nodes.py" "${COMFYUI_DEST}/"
cp "${COMFYUI_ROOT}/folder_paths.py" "${COMFYUI_DEST}/"
cp "${COMFYUI_ROOT}/execution.py" "${COMFYUI_DEST}/"
cp "${COMFYUI_ROOT}/main.py" "${COMFYUI_DEST}/"
cp "${COMFYUI_ROOT}/node_helpers.py" "${COMFYUI_DEST}/"
cp "${COMFYUI_ROOT}/comfyui_version.py" "${COMFYUI_DEST}/"

# Copy optional but useful files
if [ -f "${COMFYUI_ROOT}/extra_model_paths.yaml.example" ]; then
    cp "${COMFYUI_ROOT}/extra_model_paths.yaml.example" "${COMFYUI_DEST}/"
fi

if [ -f "${COMFYUI_ROOT}/pyproject.toml" ]; then
    cp "${COMFYUI_ROOT}/pyproject.toml" "${COMFYUI_DEST}/"
fi

# Copy additional directories that might be needed
if [ -d "${COMFYUI_ROOT}/comfy_config" ]; then
    cp -r "${COMFYUI_ROOT}/comfy_config" "${COMFYUI_DEST}/"
fi

if [ -d "${COMFYUI_ROOT}/comfy_api" ]; then
    cp -r "${COMFYUI_ROOT}/comfy_api" "${COMFYUI_DEST}/"
fi

# Copy API nodes if they exist
if [ -d "${COMFYUI_ROOT}/comfy_api_nodes" ]; then
    cp -r "${COMFYUI_ROOT}/comfy_api_nodes" "${COMFYUI_DEST}/"
fi

# Clean up __pycache__ directories
echo "Cleaning up __pycache__ directories..."
find "$COMFYUI_DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$COMFYUI_DEST" -name "*.pyc" -delete 2>/dev/null || true

echo "✅ ComfyUI files copied successfully!"
echo "📁 Destination: $COMFYUI_DEST"
echo ""
echo "Next steps:"
echo "1. Update sys.path in your service.py to include: $COMFYUI_DEST"
echo "2. Install requirements: pip install -r requirements.txt"

