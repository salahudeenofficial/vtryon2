#!/bin/bash

# Qwen Clothing Transfer v1.2 - Model Download Script
# This script downloads all the models required for the Qwen Clothing Transfer workflow
# 
# Models found in the workflow:
# 1. qwen_image_edit_fp8_e4m3fn.safetensors (UNETLoader - QWEN MODEL)
# 2. qwen_2.5_vl_7b_fp8_scaled.safetensors (CLIPLoader - QWEN CLIP)
# 3. qwen_image_vae.safetensors (VAELoader - QWEN VAE)
# 4. juggernautXL_juggXIByRundiffusion.safetensors (CheckpointLoaderSimple - SDXL CHECKPOINT)
# 5. extract-outfit_v3.safetensors (LoraLoaderModelOnly - Outfit Extractor LoRA)
# 6. clothes_tryon_qwen-edit-lora.safetensors (LoraLoaderModelOnly - Clothes Try On LoRA)
# 7. RealESRGAN_x2plus.pth (UpscaleModelLoader - UPSCALE MODEL)
# 8. Qwen-Image-Lightning-4steps-V2.0.safetensors (LoraLoaderModelOnly - Lighting LoRA)

set -e  # Exit on any error

# Configuration
COMFYUI_BASE_DIR="${COMFYUI_BASE_DIR:-$HOME/ComfyUI}"
MODELS_DIR="./models"

# Create necessary directories
echo "Creating model directories..."
mkdir -p "$MODELS_DIR/diffusion_models"
mkdir -p "$MODELS_DIR/clip"
mkdir -p "$MODELS_DIR/vae"
mkdir -p "$MODELS_DIR/checkpoints"
mkdir -p "$MODELS_DIR/loras"
mkdir -p "$MODELS_DIR/upscale_models"

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

# Model URLs (some are placeholders that need to be updated)
declare -A MODELS=(
    # Qwen Models - These are the main models for the workflow
    ["qwen_image_edit_2509_fp8_e4m3fn.safetensors"]="https://huggingface.co/theunlikely/Qwen-Image-Edit-2509/resolve/main/qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    ["qwen_image_edit_fp8_e4m3fn.safetensors"]="https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors"
    ["qwen_2.5_vl_7b_fp8_scaled.safetensors"]="https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"
    ["qwen_image_vae.safetensors"]="https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"
    
    # SDXL Checkpoint - This is a known model
    ["juggernautXL_juggXIByRundiffusion.safetensors"]="https://huggingface.co/misri/juggernautXL_juggXIByRundiffusion/resolve/main/juggernautXL_juggXIByRundiffusion.safetensors"
    
    # Upscale Model - RealESRGAN is a well-known upscaling model
    ["RealESRGAN_x2plus.pth"]="https://huggingface.co/dtarnow/UPscaler/resolve/main/RealESRGAN_x2plus.pth"
    
    # LoRA Models - These URLs need to be verified/updated
    ["extract-outfit_v3.safetensors"]="https://civitai.com/api/download/models/2196307?type=Model&format=SafeTensor"
    ["clothes_tryon_qwen-edit-lora.safetensors"]="https://civitai.com/api/download/models/2196278?type=Model&format=SafeTensor"
    ["Qwen-Image-Lightning-4steps-V2.0.safetensors"]="https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-4steps-V2.0.safetensors"
)

# Download models
echo "Starting model downloads..."
echo "=========================================="

# Download Qwen models
download_model "${MODELS[qwen_image_edit_2509_fp8_e4m3fn.safetensors]}" "$MODELS_DIR/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors" "Qwen Image Edit Model (2509)"
download_model "${MODELS[qwen_image_edit_fp8_e4m3fn.safetensors]}" "$MODELS_DIR/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors" "Qwen Image Edit Model"
download_model "${MODELS[qwen_2.5_vl_7b_fp8_scaled.safetensors]}" "$MODELS_DIR/clip/qwen_2.5_vl_7b_fp8_scaled.safetensors" "Qwen CLIP Model"
download_model "${MODELS[qwen_image_vae.safetensors]}" "$MODELS_DIR/vae/qwen_image_vae.safetensors" "Qwen VAE Model"

# Download SDXL checkpoint
download_model "${MODELS[juggernautXL_juggXIByRundiffusion.safetensors]}" "$MODELS_DIR/checkpoints/juggernautXL_juggXIByRundiffusion.safetensors" "JuggernautXL SDXL Checkpoint"

# Download upscale model
download_model "${MODELS[RealESRGAN_x2plus.pth]}" "$MODELS_DIR/upscale_models/RealESRGAN_x2plus.pth" "RealESRGAN Upscale Model"

# Download LoRA models
download_model "${MODELS[extract-outfit_v3.safetensors]}" "$MODELS_DIR/loras/extract-outfit_v3.safetensors" "Outfit Extractor LoRA"
download_model "${MODELS[clothes_tryon_qwen-edit-lora.safetensors]}" "$MODELS_DIR/loras/clothes_tryon_qwen-edit-lora.safetensors" "Clothes Try On LoRA"
download_model "${MODELS[Qwen-Image-Lightning-4steps-V2.0.safetensors]}" "$MODELS_DIR/loras/Qwen-Image-Lightning-4steps-V2.0.safetensors" "Lighting LoRA"

echo "=========================================="
echo "=========================================="
echo "📋 SUMMARY"
echo "=========================================="
echo "Successfully downloaded models:"
echo "✓ Qwen Image Edit Model"
echo "✓ Qwen CLIP Model"
echo "✓ Qwen VAE Model"
echo "✓ JuggernautXL SDXL Checkpoint"
echo "✓ RealESRGAN Upscale Model"
echo "✓ Outfit Extractor LoRA"
echo "✓ Clothes Try On LoRA"
echo "✓ Lighting LoRA"
echo ""
echo "All models have been downloaded and placed in: $MODELS_DIR"
echo ""
echo "=========================================="
echo "Downloading StableVITON checkpoints..."
echo "=========================================="
bash download_stableviton.sh
echo ""
echo "=========================================="
echo "📋 ALL DOWNLOADS COMPLETE"
echo "=========================================="
echo "You can now load the 'Qwen Clothing Transfer v1.2.json' workflow in ComfyUI."
echo "=========================================="


sed -i "s/version=get_version(),/version='1.4.2',/" setup.py

# 2. Install in editable mode
pip install -e .

git clone https://github.com/xinntao/BasicSR.git
cd BasicSR