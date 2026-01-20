#!/bin/bash
# FLUX.2 Klein Virtual Try-On POC - Quick Start Script

set -e

echo "================================================"
echo "  FLUX.2 [klein] 9B Virtual Try-On POC"
echo "================================================"
echo ""

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies
echo ""
echo "Installing base dependencies..."
pip install -q -r requirements.txt

# Install latest diffusers from git for FLUX.2 support
echo ""
echo "Installing latest diffusers from git (for FLUX.2 support)..."
pip install -q git+https://github.com/huggingface/diffusers.git

# Check HuggingFace login
echo ""
echo "Checking HuggingFace authentication..."
if ! huggingface-cli whoami > /dev/null 2>&1; then
    echo "WARNING: Not logged in to HuggingFace!"
    echo "Please run: huggingface-cli login"
    echo "And accept the model license at:"
    echo "https://huggingface.co/black-forest-labs/FLUX.2-klein-9B"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "HuggingFace authentication OK"
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "================================================"
echo "Starting server..."
echo "================================================"
echo ""
echo "Server will be available at:"
echo "  Local:  http://localhost:8000"
echo "  Remote: http://${SERVER_IP}:8000"
echo ""
echo "API Documentation: http://${SERVER_IP}:8000/docs"
echo ""
echo "Open index.html in your browser and configure"
echo "the server URL to connect."
echo ""
echo "Press Ctrl+C to stop the server."
echo "================================================"
echo ""

# Run server
python server.py
