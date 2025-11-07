#!/bin/bash

# setup.sh - Setup ComfyUI modules and download models for sampling service
# This script clones necessary ComfyUI modules from master branch and downloads required models

set -e  # Exit on any error

# Configuration
COMFYUI_ROOT="${COMFYUI_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MICROSERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DEST="${MICROSERVICE_DIR}/comfyui"
MODELS_DIR="${MICROSERVICE_DIR}/models"
VENV_DIR="${MICROSERVICE_DIR}/venv"
PYTHON_VERSION="3.13"

echo "=========================================="
echo "Sampling Service Setup"
echo "=========================================="
echo "ComfyUI Root: $COMFYUI_ROOT"
echo "Microservice Dir: $MICROSERVICE_DIR"
echo "ComfyUI Destination: $COMFYUI_DEST"
echo "Models Directory: $MODELS_DIR"
echo "Virtual Environment: $VENV_DIR"
echo "=========================================="
echo ""

# Step 0: Create Python 3.13 virtual environment
echo "Step 0: Creating Python ${PYTHON_VERSION} virtual environment..."
echo "---------------------------------------------------"

# Check if Python 3.13 is available
if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_CMD=$(command -v python3.13)
    echo "Found Python 3.13"
elif command -v python${PYTHON_VERSION} >/dev/null 2>&1; then
    PYTHON_CMD=$(command -v python${PYTHON_VERSION})
    echo "Found Python ${PYTHON_VERSION}"
else
    echo "⚠️  Python ${PYTHON_VERSION} not found. Checking for python3..."
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD=$(command -v python3)
        PYTHON_VERSION_CHECK=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        echo "Found Python $PYTHON_VERSION_CHECK"
        
        # Simple version check: extract major.minor and compare
        MAJOR=$(echo "$PYTHON_VERSION_CHECK" | cut -d. -f1)
        MINOR=$(echo "$PYTHON_VERSION_CHECK" | cut -d. -f2)
        
        if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
            echo "❌ Python 3.8+ required. Found Python $PYTHON_VERSION_CHECK"
            exit 1
        fi
    else
        echo "❌ Python 3 not found. Please install Python 3.8 or later."
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip >/dev/null 2>&1 || true

# Install PyTorch with CUDA 13.0
echo "Installing PyTorch with CUDA 13.0..."
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130 || {
    echo "⚠️  Failed to install PyTorch with CUDA 13.0, trying default PyTorch..."
    pip install torch torchvision torchaudio || {
        echo "❌ Failed to install PyTorch"
        exit 1
    }
}
echo "✓ PyTorch installed"

echo ""

# Step 1: Clone ComfyUI modules from master branch
echo "=========================================="
echo "Step 1: Cloning ComfyUI modules from master branch"
echo "=========================================="

# Check if we're in a git repository
if [ ! -d "$COMFYUI_ROOT/.git" ]; then
    echo "⚠️  Not a git repository. Trying to find ComfyUI files in current directory..."
    COMFYUI_ROOT="$MICROSERVICE_DIR/../.."
fi

# Remove existing comfyui directory if it exists
if [ -d "$COMFYUI_DEST" ]; then
    echo "Removing existing comfyui directory..."
    rm -rf "$COMFYUI_DEST"
fi

# Create comfyui directory
mkdir -p "$COMFYUI_DEST"

# Core directories to clone
core_dirs=(
    "comfy"
    "comfy_api"
    "comfy_api_nodes"
    "comfy_config"
    "comfy_execution"
    "comfy_extras"
    "custom_nodes"
    "utils"
)

echo "Cloning core ComfyUI directories..."
for dir in "${core_dirs[@]}"; do
    if [ -d "$COMFYUI_ROOT/$dir" ]; then
        echo "  Cloning $dir..."
        cp -r "$COMFYUI_ROOT/$dir" "$COMFYUI_DEST/"
        echo "  ✓ $dir cloned"
    else
        echo "  ⚠️  $dir not found in $COMFYUI_ROOT, skipping..."
    fi
done

# Essential Python files to clone
essential_files=(
    "nodes.py"
    "folder_paths.py"
    "main.py"
    "requirements.txt"
)

echo "Cloning essential Python files..."
for file in "${essential_files[@]}"; do
    if [ -f "$COMFYUI_ROOT/$file" ]; then
        echo "  Cloning $file..."
        cp "$COMFYUI_ROOT/$file" "$COMFYUI_DEST/"
        echo "  ✓ $file cloned"
    else
        echo "  ⚠️  $file not found in $COMFYUI_ROOT, skipping..."
    fi
done

# Clone requirements.txt from master branch if in git repo
if [ -d "$COMFYUI_ROOT/.git" ]; then
    echo "  Cloning requirements.txt from master branch..."
    git -C "$COMFYUI_ROOT" show master:requirements.txt > "$COMFYUI_DEST/requirements.txt" 2>/dev/null || {
        if [ -f "$COMFYUI_ROOT/requirements.txt" ]; then
            cp "$COMFYUI_ROOT/requirements.txt" "$COMFYUI_DEST/requirements.txt"
        fi
    }
    echo "  ✓ requirements.txt cloned"
elif [ -f "$COMFYUI_ROOT/requirements.txt" ]; then
    echo "  Copying requirements.txt from current working tree..."
    cp "$COMFYUI_ROOT/requirements.txt" "$COMFYUI_DEST/requirements.txt"
    echo "  ✓ requirements.txt copied"
fi

# Clone optional files
optional_files=(
    "extra_model_paths.yaml.example"
    "pyproject.toml"
)

for file in "${optional_files[@]}"; do
    if [ -f "$COMFYUI_ROOT/$file" ]; then
        cp "$COMFYUI_ROOT/$file" "$COMFYUI_DEST/$file" 2>/dev/null || true
    fi
done

# Clean up __pycache__ directories
echo "Cleaning up cache files..."
find "$COMFYUI_DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$COMFYUI_DEST" -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "✓ ComfyUI modules cloned successfully!"
echo ""

# Step 1.5: Update requirements.txt with additional dependencies
echo "Step 1.5: Adding additional dependencies to requirements.txt..."
echo "---------------------------------------------------"

REQUIREMENTS_FILE="${MICROSERVICE_DIR}/requirements.txt"
COMFYUI_REQUIREMENTS="${COMFYUI_DEST}/requirements.txt"

# Copy ComfyUI requirements.txt to microservice directory
if [ -f "$COMFYUI_REQUIREMENTS" ]; then
    cp "$COMFYUI_REQUIREMENTS" "$REQUIREMENTS_FILE"
    echo "✓ Copied ComfyUI requirements.txt"
else
    echo "⚠️  ComfyUI requirements.txt not found, creating new file..."
    touch "$REQUIREMENTS_FILE"
fi

# Additional dependencies for sampling microservice
ADDITIONAL_DEPS=(
    "# Additional packages required for sampling microservice"
    "confluent-kafka>=2.3.0"
    "python-dotenv>=1.0.0"
    "pydantic>=2.0.0"
)

# Check if additional dependencies are already in the file
NEEDS_UPDATE=true
if [ -f "$REQUIREMENTS_FILE" ]; then
    if grep -q "confluent-kafka" "$REQUIREMENTS_FILE"; then
        echo "✓ Additional dependencies already present in requirements.txt"
        NEEDS_UPDATE=false
    fi
fi

# Append additional dependencies if needed
if [ "$NEEDS_UPDATE" = true ]; then
    echo "" >> "$REQUIREMENTS_FILE"
    echo "" >> "$REQUIREMENTS_FILE"
    for dep in "${ADDITIONAL_DEPS[@]}"; do
        echo "$dep" >> "$REQUIREMENTS_FILE"
    done
    echo "✓ Added additional dependencies to requirements.txt"
fi

echo "Requirements file: $REQUIREMENTS_FILE"
echo ""

# Step 1.6: Install requirements.txt
echo "Step 1.6: Installing requirements from requirements.txt..."
echo "---------------------------------------------------"

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Install requirements
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing packages from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE" || {
        echo "⚠️  Some packages failed to install. Continuing anyway..."
    }
    echo "✓ Requirements installed"
else
    echo "⚠️  requirements.txt not found, skipping installation"
fi

echo ""

# Step 2: Download models
echo "=========================================="
echo "Step 2: Downloading required models"
echo "=========================================="

# Create model directories
mkdir -p "$MODELS_DIR/diffusion_models"
mkdir -p "$MODELS_DIR/loras"

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
    ["qwen_image_edit_2509_fp8_e4m3fn.safetensors"]="https://huggingface.co/theunlikely/Qwen-Image-Edit-2509/resolve/main/qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    ["Qwen-Image-Lightning-4steps-V2.0.safetensors"]="https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-4steps-V2.0.safetensors"
)

# Download UNET model
download_model "${MODELS[qwen_image_edit_2509_fp8_e4m3fn.safetensors]}" "$MODELS_DIR/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors" "Qwen UNET Model"

# Download LoRA model
download_model "${MODELS[Qwen-Image-Lightning-4steps-V2.0.safetensors]}" "$MODELS_DIR/loras/Qwen-Image-Lightning-4steps-V2.0.safetensors" "Qwen Lightning LoRA Model"

echo ""
echo "=========================================="
echo "=========================================="
echo "📋 SETUP COMPLETE"
echo "=========================================="
echo "✓ Python virtual environment created and activated"
echo "✓ PyTorch with CUDA 13.0 installed"
echo "✓ ComfyUI modules cloned from master branch"
echo "✓ Requirements.txt updated with additional dependencies"
echo "✓ All requirements installed"
echo "✓ Models downloaded (UNET + LoRA)"
echo ""
echo "Virtual environment: $VENV_DIR"
echo "ComfyUI modules: $COMFYUI_DEST"
echo "Models directory: $MODELS_DIR"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo ""
echo "2. Test the service:"
echo "   python main.py --mode standalone \\"
echo "     --positive_encoding <path_to_positive.pt> \\"
echo "     --negative_encoding <path_to_negative.pt> \\"
echo "     --latent_image <path_to_latent.pt> \\"
echo "     --seed 12345"
echo ""
echo "Note: Always activate the virtual environment before running the service:"
echo "   source venv/bin/activate"
echo ""
echo "Note: All dependencies have been installed from requirements.txt"
echo "      (ComfyUI base requirements + microservice additions)"
echo "=========================================="



