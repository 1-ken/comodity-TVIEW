# Postman API Testing Guide

This guide explains how to import and use the Postman collection to test all Commodities Observer API endpoints.

## Files Created

1. **commodities-api.postman_collection.json** - Complete API endpoint collection with 15+ endpoints
2. **postman-environment.json** - Environment variables for local testing
3. **WEBSOCKET_TESTING.md** - Guide for WebSocket endpoint testing

## Prerequisites

- **Postman** installed ([Download](https://www.postman.com/downloads/))
- **Commodities Observer backend** running on `http://localhost:8001`
- Python 3.13+ with project dependencies installed

## Setup Instructions

### Step 1: Start the Backend Server

```bash
# Activate virtual environment
source /home/here/Desktop/prompts/commodities/.venv/bin/activate

# Start the server
python run.py
```

Expected output:
```
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### Step 2: Import Collection into Postman

1. Open **Postman**
2. Click **File** → **Import** (or Ctrl+O)
3. Select **Upload Files**
4. Navigate to: `/home/here/Desktop/prompts/commodities/commodities-api.postman_collection.json`
5. Click **Import**

The collection will appear in your sidebar with folders:
- **Price Data** - Snapshot and config endpoints
- **Alerts** - Alert CRUD operations
- **Replay** - Price history replay controls
- **WebSocket** - Real-time streaming (see WEBSOCKET_TESTING.md)

### Step 3: Import Environment Variables

1. Click **Environments** (top left)
2. Click **Import**
3. Select: `/home/here/Desktop/prompts/commodities/postman-environment.json`
4. Click **Import**

The environment will be added with variables:
- `base_url`: `http://localhost:8001`
- `ws_url`: `ws://localhost:8001/ws/observe`
- `email`: `test@example.com`
- `phone`: `+1234567890`
- `test_pair`: `EURUSD`
- `test_target_price`: `1.0850`

### Step 4: Select Environment

1. In the top right, select **"Commodities Observer - Local"** from the environment dropdown
2. All collection requests will now use the configured `{{base_url}}` and other variables

## CORS Configuration

✅ **CORS is enabled** on the backend with:
- **Allowed Origins**: All (`*`)
- **Allowed Methods**: GET, POST, DELETE, OPTIONS
- **Allowed Headers**: All (`*`)

This allows requests from any domain, including Postman.

## Testing the Endpoints

### 1. Test Basic Price Data

1. **Get Current Snapshot**
   - Click: Collections → Price Data → Get Current Snapshot
   - Click **Send**
   - Expected: 200 OK response with commodity prices

2. **Get Client Config**
   - Click: Collections → Price Data → Get Client Config
   - Click **Send**
   - Expected: WebSocket URL configuration

### 2. Create and Manage Alerts

1. **Create Alert (Email)**
   - Click: Collections → Alerts → Create Alert - Email
   - Review the request body
   - Click **Send**
   - Expected: 200 OK with alert object containing `id`
   - **Save the alert ID** for later tests

2. **Get All Alerts**
   - Click: Collections → Alerts → Get All Alerts
   - Click **Send**
   - Expected: List of all active and triggered alerts

3. **Get Single Alert**
   - Set `alert_id` variable or paste ID in path
   - Click: Collections → Alerts → Get Alert by ID
   - Click **Send**
   - Expected: Details of the specific alert

4. **Delete Alert**
   - Click: Collections → Alerts → Delete Alert
   - Click **Send**
   - Expected: 200 OK with success message

### 3. Test Price History Replay

1. **Get Replay Info**
   - Click: Collections → Replay → Get Replay Info
   - Click **Send**
   - Expected: Total snapshots and date range

2. **Get Price History**
   - Click: Collections → Replay → Get Price History
   - Click **Send**
   - Expected: Recent price snapshots (last 100)

3. **Start Replay**
   - Click: Collections → Replay → Start Replay
   - Click **Send**
   - Expected: Replay status showing `state: "playing"`

4. **Control Replay**
   - **Pause**: Collections → Replay → Pause Replay
   - **Resume**: Collections → Replay → Resume Replay
   - **Stop**: Collections → Replay → Stop Replay
   - **Set Speed**: Collections → Replay → Set Replay Speed (change `speed` param)
   - **Seek by Index**: Collections → Replay → Seek Replay by Index
   - **Seek by Percentage**: Collections → Replay → Seek Replay by Percentage

5. **Get Replay Status**
   - Click: Collections → Replay → Get Replay Status
   - Click **Send**
   - Expected: Current replay state, progress, and speed

## Testing WebSocket

WebSocket endpoints cannot be tested directly in Postman. Use one of these alternatives:

### Python (Recommended)

```bash
# Install websockets library
pip install websockets

# Save this as test_ws.py
python3 WEBSOCKET_TESTING.md  # Or copy the Python example
```

### Using websocat (CLI Tool)

```bash
# Install websocat
brew install websocat  # macOS
# or
sudo apt-get install websocat  # Linux

# Connect to WebSocket
websocat ws://localhost:8001/ws/observe
```

### Browser Console

Open browser DevTools (F12) and paste:
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/observe');
ws.onmessage = e => console.log(JSON.parse(e.data));
```

See **WEBSOCKET_TESTING.md** for complete WebSocket testing examples.

## Advanced Testing Scenarios

### Scenario 1: Create Alert and Monitor via WebSocket

1. Create an alert via REST API (Alerts → Create Alert)
2. Connect to WebSocket via Python/websocat
3. Observe the alert appearing in WebSocket messages
4. In browser/app, trigger the condition
5. Observe alert moving from "active" to "triggered" in WebSocket stream

### Scenario 2: Replay with Speed Control

1. Start replay (Replay → Start Replay with `speed=1.0`)
2. Set speed to 2x (Replay → Set Replay Speed with `speed=2.0`)
3. Pause replay (Replay → Pause Replay)
4. Seek to 50% (Replay → Seek Replay by Percentage with `percent=50`)
5. Resume (Replay → Resume Replay)
6. Stop (Replay → Stop Replay)

### Scenario 3: Monitor Real-time Alerts

1. Connect to WebSocket
2. Create multiple alerts with different conditions
3. Watch alerts appear in the active list
4. Prices update every second in WebSocket stream
5. Triggered alerts move to triggered list automatically

## Troubleshooting

### ❌ "Cannot connect to localhost:8001"
- Ensure backend is running: `python run.py`
- Check firewall settings
- Verify backend is listening on port 8001

### ❌ "CORS error in browser"
- CORS is properly configured in the backend
- Error might be from different origin than expected
- Check browser console for specific error

### ❌ "Alert validation error"
- Ensure condition is one of: "above", "below", "equal"
- If using SMS, phone number is required
- If using email, email address is required
- At least one channel (email/sms) must be selected

### ❌ "No price history available"
- Server needs time to collect snapshots
- Wait at least 1-2 minutes after startup
- Check snapshot endpoint returns data

## Response Examples

### Alert Object
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "pair": "EURUSD",
  "target_price": 1.0850,
  "condition": "above",
  "status": "active",
  "created_at": "2026-02-10T12:00:00Z",
  "channels": ["email"],
  "email": "user@example.com",
  "phone": "",
  "custom_message": "EUR/USD has moved above 1.0850!",
  "triggered_at": null,
  "last_checked_price": 1.0842
}
```

### Price Snapshot
```json
{
  "pairs": [
    {
      "pair": "SPX",
      "price": "6952.59",
      "timestamp": "2026-02-10T12:34:56.789Z"
    },
    {
      "pair": "GOLD",
      "price": "2050.50",
      "timestamp": "2026-02-10T12:34:56.789Z"
    }
  ],
  "ts": "2026-02-10T12:34:56.789Z"
}
```

### Replay Status
```json
{
  "state": "playing",
  "current_index": 45,
  "total_snapshots": 100,
  "progress_percent": 45.0,
  "speed": 1.0,
  "is_playing": true,
  "is_paused": false,
  "is_stopped": false
}
```

## Tips for Testing

1. **Save alert IDs**: When creating alerts, save the ID from the response to use in subsequent tests
2. **Use variables**: Customize `email`, `phone`, and `test_pair` in environment for your testing
3. **Monitor logs**: Watch backend logs while testing to see detailed error messages
4. **Test WebSocket separately**: Use Python/websocat for WebSocket testing (see WEBSOCKET_TESTING.md)
5. **Batch test**: Create multiple alerts then test retrieval and deletion
6. **Speed up replay**: Use high speed values (2.0-4.0) for faster playback

## API Documentation

For detailed API documentation, run the server and visit:
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

Both provide interactive API documentation with request/response examples.

---

**Need help?** Check the server logs:
```bash
tail -f run.log  # If available
```
