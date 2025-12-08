# Troubleshooting Guide

## Issue: uvicorn command shows ComfyUI arguments

### Problem
When running:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You see ComfyUI's uvicorn help text with arguments like `--listen`, `--port`, `--cuda-device`, etc., instead of the standard uvicorn arguments.

### Root Cause
ComfyUI has its own `main.py` file that wraps uvicorn with custom arguments. When you run `uvicorn` from the command line, the system may pick up ComfyUI's wrapper instead of the standard uvicorn package.

### Solution

**Always use `python run_server.py` instead:**

```bash
python run_server.py
```

This script:
- Imports uvicorn directly in Python (avoiding command-line conflicts)
- Properly sets up the Python path
- Avoids conflicts with ComfyUI's main.py

### Alternative Solutions

If you must use uvicorn directly, use the Python module syntax:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

This ensures Python uses the installed uvicorn module rather than any command-line wrapper.

### Verification

After starting the server, verify it's running:

```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "ok",
  "gpu_available": true,
  "model_loaded": true,
  "node_id": "qwen-gpu-1"
}
```

