# Ngrok Setup for Asset Service

## Quick Setup

1. **Install ngrok** (if not already installed):
   ```bash
   # Option 1: Using snap (if available)
   snap install ngrok
   
   # Option 2: Download from https://ngrok.com/download
   ```

2. **Sign up and get authtoken**:
   - Go to https://dashboard.ngrok.com/signup
   - Sign up for a free account
   - Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken

3. **Configure ngrok**:
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

4. **Start Asset Service** (in one terminal):
   ```bash
   python test_asset_service.py
   ```

5. **Start ngrok tunnel** (in another terminal):
   ```bash
   ngrok http 8001
   ```

6. **Get the ngrok URL**:
   - Look for the "Forwarding" line in ngrok output
   - Example: `https://abc123.ngrok-free.app -> http://localhost:8001`
   - Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

7. **Update config.yaml**:
   ```yaml
   asset_service:
     callback_url: "https://abc123.ngrok-free.app/v1/vton/result"
   ```

8. **Restart GPU server** with updated config

## Alternative: Using ngrok API

You can also get the URL programmatically:
```bash
curl http://localhost:4040/api/tunnels | python3 -m json.tool
```

Look for the `public_url` field in the response.

## Notes

- Free ngrok URLs change each time you restart ngrok
- For production, consider using a static domain or paid ngrok plan
- Keep ngrok running while testing
- The Asset Service must be running before starting ngrok

