#!/usr/bin/env python3
"""
Entry point for running the GPU server.
This avoids conflicts with ComfyUI's main.py
"""
import sys
import os
from pathlib import Path

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

