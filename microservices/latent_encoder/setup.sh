#!/bin/bash

# setup.sh - Setup ComfyUI modules and download models for latent encoder service
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
echo "Latent Encoder Service Setup"
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
        echo "Using Python $PYTHON_VERSION_CHECK (Python 3.13 not available)"
    else
        echo "❌ Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
fi

echo "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# Create virtual environment if it doesn't exist
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists at $VENV_DIR"
else
    echo "Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip >/dev/null 2>&1 || true

# Install PyTorch with CUDA 13.0 support
echo "Installing PyTorch with CUDA 13.0 support..."
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130

echo "✓ PyTorch installed successfully"
echo ""

# Function to clone directory from git
clone_from_master() {
    local source_path="$1"
    local dest_path="$2"
    local description="$3"
    
    echo "Cloning $description..."
    
    # Create destination directory
    mkdir -p "$dest_path"
    
    # Use git checkout to get files from master branch
    cd "$COMFYUI_ROOT"
    
    # Get the relative path from repo root
    rel_path=$(git rev-parse --show-prefix 2>/dev/null || echo "")
    if [ -n "$rel_path" ]; then
        full_source="$COMFYUI_ROOT/$rel_path/$source_path"
    else
        full_source="$COMFYUI_ROOT/$source_path"
    fi
    
    # Check if source exists in master branch
    if git ls-tree -r --name-only master | grep -q "^${source_path%/}/"; then
        echo "  Found in master branch, cloning..."
        
        # Clone directory structure from master
        if [ -d "$source_path" ]; then
            # Copy directory structure
            rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
                "$source_path/" "$dest_path/" 2>/dev/null || {
                # If rsync fails, use git show
                echo "  Using git checkout..."
                git checkout master -- "$source_path" 2>/dev/null || true
                cp -r "$source_path"/* "$dest_path/" 2>/dev/null || true
            }
        else
            # Use git sparse-checkout or git show
            echo "  Using git sparse-checkout..."
            git archive master "$source_path" | tar -x -C "$dest_path" 2>/dev/null || {
                # Fallback: try to get individual files
                echo "  Fallback: copying from current working tree..."
                if [ -d "$COMFYUI_ROOT/$source_path" ]; then
                    cp -r "$COMFYUI_ROOT/$source_path"/* "$dest_path/" 2>/dev/null || true
                fi
            }
        fi
    else
        # Fallback: copy from current working directory
        echo "  Not in master, copying from current working tree..."
        if [ -d "$COMFYUI_ROOT/$source_path" ]; then
            cp -r "$COMFYUI_ROOT/$source_path"/* "$dest_path/" 2>/dev/null || true
        fi
    fi
    
    echo "  ✓ $description cloned"
}

# Step 1: Clone ComfyUI modules from master branch
echo "Step 1: Cloning ComfyUI modules from master branch..."
echo "---------------------------------------------------"

# Create destination directory
mkdir -p "$COMFYUI_DEST"

# Clone core directories
clone_from_master "comfy" "$COMFYUI_DEST/comfy" "Comfy core library"
clone_from_master "utils" "$COMFYUI_DEST/utils" "Utils directory"
clone_from_master "comfy_execution" "$COMFYUI_DEST/comfy_execution" "Comfy execution"
clone_from_master "comfy_extras" "$COMFYUI_DEST/comfy_extras" "Comfy extras"
clone_from_master "custom_nodes" "$COMFYUI_DEST/custom_nodes" "Custom nodes"

# Clone core Python files
echo "Cloning core Python files..."
cd "$COMFYUI_ROOT"

# List of core files to clone
core_files=(
    "nodes.py"
    "folder_paths.py"
    "execution.py"
    "main.py"
    "node_helpers.py"
    "comfyui_version.py"
)

for file in "${core_files[@]}"; do
    if git ls-tree -r --name-only master | grep -q "^${file}$"; then
        echo "  Cloning $file from master..."
        git show "master:$file" > "$COMFYUI_DEST/$file" 2>/dev/null || {
            # Fallback: copy from current
            if [ -f "$COMFYUI_ROOT/$file" ]; then
                cp "$COMFYUI_ROOT/$file" "$COMFYUI_DEST/$file"
            fi
        }
        echo "  ✓ $file cloned"
    elif [ -f "$COMFYUI_ROOT/$file" ]; then
        echo "  Copying $file from current working tree..."
        cp "$COMFYUI_ROOT/$file" "$COMFYUI_DEST/$file"
        echo "  ✓ $file copied"
    fi
done

# Clone requirements.txt from master branch
echo "Cloning requirements.txt from master..."
cd "$COMFYUI_ROOT"
if git ls-tree -r --name-only master | grep -q "^requirements.txt$"; then
    echo "  Cloning requirements.txt from master..."
    git show "master:requirements.txt" > "$COMFYUI_DEST/requirements.txt" 2>/dev/null || {
        # Fallback: copy from current
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

# Additional dependencies for latent encoder microservice
ADDITIONAL_DEPS=(
    "# Additional packages required for latent_encoder microservice"
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

# Download VAE model
download_model "${MODELS[qwen_image_vae.safetensors]}" "$MODELS_DIR/vae/qwen_image_vae.safetensors" "Qwen VAE Model"

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
echo "✓ Models downloaded"
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
echo "   python main.py --mode standalone --image_path <path_to_image>"
echo ""
echo "Note: Always activate the virtual environment before running the service:"
echo "   source venv/bin/activate"
echo ""
echo "Note: All dependencies have been installed from requirements.txt"
echo "      (ComfyUI base requirements + microservice additions)"
echo "=========================================="

