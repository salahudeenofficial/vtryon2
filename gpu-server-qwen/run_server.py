#!/usr/bin/env python3
"""
Entry point for running the GPU server.
This avoids conflicts with ComfyUI's main.py
"""
import sys
import os
from pathlib import Path

# ============================================================================
# CRITICAL: Set ComfyUI flags BEFORE any other imports
# ============================================================================
# These must be set before any module imports comfy.cli_args

# GPU-only mode: keep all models in VRAM (requires 48GB+ GPU like L40S)
if '--highvram' not in sys.argv:
    sys.argv.append('--highvram')
if '--disable-smart-memory' not in sys.argv:
    sys.argv.append('--disable-smart-memory')

# PyTorch native attention (faster than split attention)
if '--use-pytorch-cross-attention' not in sys.argv:
    sys.argv.append('--use-pytorch-cross-attention')

print(f"[GPU-ONLY MODE] sys.argv flags set: --highvram, --disable-smart-memory, --use-pytorch-cross-attention")

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
