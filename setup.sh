#!/bin/bash

# setup.sh - Complete setup script for Virtual Try-On API
# This script:
# 1. Creates Python 3.13 virtual environment
# 2. Installs PyTorch with CUDA 13.0
# 3. Downloads all required models
# 4. Installs basicsr
# 5. Installs requirements from requirements.txt
# 6. Starts the FastAPI server

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
PYTHON_VERSION="3.13"

echo "=========================================="
echo "Virtual Try-On API - Complete Setup"
echo "=========================================="
echo "Script directory: ${SCRIPT_DIR}"
echo "Virtual environment: ${VENV_DIR}"
echo "Python version: ${PYTHON_VERSION}"
echo "=========================================="
echo ""

# # Step 1: Create Python 3.13 virtual environment
# echo "Step 1: Creating Python ${PYTHON_VERSION} virtual environment..."
# echo "---------------------------------------------------"

# # Check if Python 3.13 is available
# if command -v python3.13 >/dev/null 2>&1; then
#     PYTHON_CMD=$(command -v python3.13)
#     echo "Found Python 3.13"
# elif command -v python${PYTHON_VERSION} >/dev/null 2>&1; then
#     PYTHON_CMD=$(command -v python${PYTHON_VERSION})
#     echo "Found Python ${PYTHON_VERSION}"
# else
#     echo "⚠️  Python ${PYTHON_VERSION} not found. Checking for python3..."
#     if command -v python3 >/dev/null 2>&1; then
#         PYTHON_CMD=$(command -v python3)
#         PYTHON_VERSION_CHECK=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
#         echo "Found Python $PYTHON_VERSION_CHECK"
        
#         # Simple version check: extract major.minor and compare
#         MAJOR=$(echo "$PYTHON_VERSION_CHECK" | cut -d. -f1)
#         MINOR=$(echo "$PYTHON_VERSION_CHECK" | cut -d. -f2)
        
#         if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
#             echo "❌ Python 3.8+ required. Found Python $PYTHON_VERSION_CHECK"
#             exit 1
#         fi
#     else
#         echo "❌ Python 3 not found. Please install Python 3.8 or later."
#         exit 1
#     fi
# fi

# # Create virtual environment if it doesn't exist
# if [ ! -d "$VENV_DIR" ]; then
#     echo "Creating virtual environment..."
#     $PYTHON_CMD -m venv "$VENV_DIR"
#     echo "✓ Virtual environment created"
# else
#     echo "✓ Virtual environment already exists"
# fi

# # Activate virtual environment
# echo "Activating virtual environment..."
# source "$VENV_DIR/bin/activate"

# # Upgrade pip
# echo "Upgrading pip..."
# pip install --upgrade pip >/dev/null 2>&1 || true

# echo ""

# # Step 2: Install PyTorch with CUDA 13.0
# echo "Step 2: Installing PyTorch with CUDA 13.0..."
# echo "---------------------------------------------------"
# pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130 || {
#     echo "⚠️  Failed to install PyTorch with CUDA 13.0, trying default PyTorch..."
#     pip install torch torchvision torchaudio || {
#         echo "❌ Failed to install PyTorch"
#         exit 1
#     }
# }
# echo "✓ PyTorch installed"

# echo ""

# # Step 3: Download all models
# echo "Step 3: Downloading all required models..."
# echo "---------------------------------------------------"
# echo "This may take a while depending on your internet connection..."
# echo ""

# # Run download.sh to download ComfyUI models
# if [ -f "${SCRIPT_DIR}/download.sh" ]; then
#     echo "Running download.sh to download ComfyUI models..."
#     bash "${SCRIPT_DIR}/download.sh"
#     echo "✓ ComfyUI models downloaded"
# else
#     echo "⚠️  download.sh not found, skipping model downloads"
# fi

# echo ""



# Step 5: Install requirements from requirements.txt
echo "Step 5: Installing requirements from requirements.txt..."
echo "---------------------------------------------------"
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "Installing packages from requirements.txt..."
    pip install -r "${SCRIPT_DIR}/requirements.txt" || {
        echo "⚠️  Some packages failed to install. Continuing anyway..."
    }
    echo "✓ Requirements installed"
else
    echo "⚠️  requirements.txt not found, skipping installation"
fi

echo ""

# # Step 6: Install additional dependencies from mask.txt (if exists)
# echo "Step 6: Installing additional dependencies from mask.txt..."
# echo "---------------------------------------------------"
# if [ -f "${SCRIPT_DIR}/mask.txt" ]; then
#     echo "Installing packages from mask.txt..."
#     pip install -r "${SCRIPT_DIR}/mask.txt" || {
#         echo "⚠️  Some packages from mask.txt failed to install. Continuing anyway..."
#     }
#     echo "✓ Additional dependencies installed"
# else
#     echo "⚠️  mask.txt not found, skipping additional dependencies"
# fi

# echo ""

# Step 7: Verify installation
echo "Step 7: Verifying installation..."
echo "---------------------------------------------------"
echo "Checking key packages..."
python -c "import torch; print(f'✓ PyTorch {torch.__version__}')" || echo "❌ PyTorch not found"
python -c "import fastapi; print(f'✓ FastAPI {fastapi.__version__}')" || echo "❌ FastAPI not found"
python -c "import basicsr; print('✓ basicsr installed')" || echo "⚠️  basicsr not found"
python -c "import cv2; print(f'✓ OpenCV {cv2.__version__}')" || echo "⚠️  OpenCV not found"

echo ""

# Step 8: Start FastAPI server
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Starting FastAPI server..."
echo "Server will be available at: http://0.0.0.0:8000"
echo "API documentation: http://0.0.0.0:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Check if api_server.py exists
if [ ! -f "${SCRIPT_DIR}/api_server.py" ]; then
    echo "❌ api_server.py not found!"
    echo "Please ensure api_server.py exists in the current directory"
    exit 1
fi

# Start the FastAPI server
python "${SCRIPT_DIR}/api_server.py"

