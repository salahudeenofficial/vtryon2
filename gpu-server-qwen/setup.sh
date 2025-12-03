#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="./venv"
PYTHON_VERSION="3.13"
REPO_URL="https://github.com/salahudeenofficial/vtryon2.git"
REPO_DIR="vtryon2"
PORT=8000
HOST="0.0.0.0"

echo "=========================================="
echo "Qwen Image Edit API - Setup Script"
echo "=========================================="
echo ""

# --- Step 1: Check Python version ---
echo "Step 1: Checking Python version..."
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    echo "✓ Found python3.13"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION_CHECK=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION_CHECK" == "3.13" ]]; then
        PYTHON_CMD="python3"
        echo "✓ Found python3 (version 3.13)"
    else
        echo -e "${YELLOW}⚠ Warning: python3.13 not found. Using python3 (version: $PYTHON_VERSION_CHECK)${NC}"
        PYTHON_CMD="python3"
    fi
else
    echo -e "${RED}❌ Error: Python 3.13 not found. Please install Python 3.13 first.${NC}"
    exit 1
fi
echo ""

# --- Step 2: Create virtual environment ---
echo "=========================================="
echo "Step 2: Creating Python virtual environment"
echo "=========================================="
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
    echo "Skipping creation..."
else
    echo "Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi
echo ""

# --- Step 3: Activate virtual environment ---
echo "=========================================="
echo "Step 3: Activating virtual environment"
echo "=========================================="
source "$VENV_DIR/bin/activate"
echo "✓ Virtual environment activated"
echo "Python path: $(which python)"
echo "Python version: $(python --version)"
echo ""

# --- Step 5: Upgrade pip ---
echo "=========================================="
echo "Step 5: Upgrading pip"
echo "=========================================="
pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# --- Step 6: Install PyTorch with CUDA 13.0 ---
echo "=========================================="
echo "Step 6: Installing PyTorch with CUDA 13.0"
echo "=========================================="
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130 || {
    echo -e "${RED}❌ Failed to install PyTorch.${NC}"
    exit 1
}
echo "✓ PyTorch installed"
echo ""

# --- Step 7: Install requirements.txt ---
echo "=========================================="
echo "Step 7: Installing dependencies from requirements.txt"
echo "=========================================="
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || {
        echo -e "${RED}❌ Failed to install requirements.txt dependencies.${NC}"
        exit 1
    }
    echo "✓ requirements.txt dependencies installed"
else
    echo -e "${YELLOW}⚠ Warning: requirements.txt not found. Skipping...${NC}"
fi
echo ""

# --- Step 8: Run download.sh ---
echo "=========================================="
echo "Step 8: Downloading models (download.sh)"
echo "=========================================="
if [ -f "download.sh" ]; then
    bash download.sh || {
        echo -e "${YELLOW}⚠ Warning: download.sh failed or had errors. Continuing anyway...${NC}"
    }
    echo "✓ Model download completed"
else
    echo -e "${YELLOW}⚠ Warning: download.sh not found. Skipping model download...${NC}"
    echo "You may need to download models manually."
fi
echo ""

# --- Step 9: Verify key installations ---
echo "=========================================="
echo "Step 9: Verifying installations"
echo "=========================================="
echo "Checking key packages..."
python -c "import torch; print(f'✓ PyTorch {torch.__version__}')" || {
    echo -e "${RED}❌ PyTorch not properly installed.${NC}"
    exit 1
}

python -c "import fastapi; print(f'✓ FastAPI {fastapi.__version__}')" || {
    echo -e "${RED}❌ FastAPI not installed.${NC}"
    exit 1
}

python -c "import uvicorn; print(f'✓ Uvicorn installed')" || {
    echo -e "${RED}❌ Uvicorn not installed.${NC}"
    exit 1
}
echo ""

# --- Step 10: Start FastAPI server ---
echo "=========================================="
echo "Step 10: Starting FastAPI server"
echo "=========================================="
echo -e "${GREEN}Starting server on http://${HOST}:${PORT}${NC}"
echo ""
echo "API Endpoints:"
echo "  - POST /tryon - Virtual try-on endpoint"
echo "  - GET /health - Health check endpoint"
echo ""
echo "Press CTRL+C to stop the server"
echo "=========================================="
echo ""

# Start the server
python api_server.py || uvicorn api_server:app --host "$HOST" --port "$PORT"

