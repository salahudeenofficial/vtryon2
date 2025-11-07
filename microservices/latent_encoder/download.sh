#!/bin/bash

# Latent Encoder Microservice - Model Download Script
# This script downloads the VAE model required for the latent encoder service

set -e  # Exit on any error

# Configuration
MODELS_DIR="./models"

# Create necessary directories
echo "Creating model directories..."
mkdir -p "$MODELS_DIR/vae"

# Function to download with progress and error handling
download_model() {
    local url="$1"
    local output_path="$2"
    local model_name="$3"
    
    if [ -f "$output_path" ]; then
        echo "✓ $model_name already exists, skipping..."
        return 0
    fi
    
    echo "Downloading $model_name..."
    echo "URL: $url"
    echo "Output: $output_path"
    
    # Use robust wget parameters for server with connection issues
    if command -v wget >/dev/null 2>&1; then
        wget -c --timeout=0 --tries=0 --retry-connrefused --no-check-certificate --progress=bar:force:noscroll \
            -O "$output_path" "$url" || {
            echo "❌ Failed to download $model_name with wget"
            return 1
        }
    elif command -v curl >/dev/null 2>&1; then
        curl -L --retry 0 --retry-max-time 0 --connect-timeout 0 --max-time 0 -k -o "$output_path" "$url" || {
            echo "❌ Failed to download $model_name with curl"
            return 1
        }
    else
        echo "❌ Neither wget nor curl found. Please install one of them."
        return 1
    fi
    
    echo "✓ Successfully downloaded $model_name"
}

# Model URLs
declare -A MODELS=(
    ["qwen_image_vae.safetensors"]="https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"
)

# Download models
echo "Starting model downloads..."
echo "=========================================="

# Download VAE model
download_model "${MODELS[qwen_image_vae.safetensors]}" "$MODELS_DIR/vae/qwen_image_vae.safetensors" "Qwen VAE Model"

echo "=========================================="
echo "=========================================="
echo "📋 SUMMARY"
echo "=========================================="
echo "Successfully downloaded models:"
echo "✓ Qwen VAE Model"
echo ""
echo "All models have been downloaded and placed in: $MODELS_DIR"
echo ""
echo "You can now run the latent encoder service:"
echo "  python main.py --mode standalone --image_path <path_to_image>"
echo "=========================================="



