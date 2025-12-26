#!/usr/bin/env python3
"""
Entry point for running the GPU server.
This avoids conflicts with ComfyUI's main.py
"""
import sys
import os
from pathlib import Path

# ============================================================================
# Set ComfyUI optimization flags BEFORE any other imports
# ============================================================================
# GPU-only mode: forces all models to load fully into GPU memory
# This is required for optimal performance on GPUs with enough VRAM (48GB+)
if '--highvram' not in sys.argv:
    sys.argv.append('--highvram')

# PyTorch native attention (faster than split attention)
if '--use-pytorch-cross-attention' not in sys.argv:
    sys.argv.append('--use-pytorch-cross-attention')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    
    # Get the app
    from app.main import app
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,  # Use our JSON logging
    )
