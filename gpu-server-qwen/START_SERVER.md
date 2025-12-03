# How to Start the GPU Server

## Issue
When running `python -m uvicorn app.main:app`, Python may pick up ComfyUI's `main.py` instead of uvicorn, causing errors.

## Solution

### Option 1: Use the run_server.py script (Recommended)
```bash
python run_server.py
```

### Option 2: Use uvicorn directly (if installed)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Run from Python
```bash
python -c "from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"
```

## Troubleshooting

If you get errors about ComfyUI arguments:
- Use `run_server.py` instead
- Or ensure you're in the `gpu-server-qwen` directory
- Or use absolute imports

## Verify Server is Running

After starting, check:
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

