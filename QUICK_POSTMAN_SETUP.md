# 🚀 Quick Reference - Commodities Observer Backend API

## Immediate Next Steps

### 1. Start Backend Server
```bash
cd /home/here/Desktop/prompts/commodities
source .venv/bin/activate
python run.py
```
✅ Server will be available at: `http://localhost:8001`

### 2. Import to Postman (2 minutes)
1. Open Postman
2. **File** → **Import**
3. Select: `commodities-api.postman_collection.json`
4. **File** → **Import** again
5. Select: `postman-environment.json`
6. Select environment: **Commodities Observer - Local**

### 3. Test First Endpoint (1 minute)
1. Collections → **Price Data** → **Get Current Snapshot**
2. Click **Send**
3. ✅ Response: 200 OK with prices

---

## 📋 All Available Endpoints

### Price Data (2)
- `GET /snapshot` - Current prices
- `GET /client-config` - WebSocket URL

### Alerts (6)
- `POST /api/alerts` - Create alert
- `GET /api/alerts` - Get all alerts
- `GET /api/alerts/{id}` - Get alert
- `DELETE /api/alerts/{id}` - Delete alert

### Replay (10)
- `GET /api/replay/info` - Info
- `GET /api/replay/history` - Snapshots
- `POST /api/replay/start` - Start
- `POST /api/replay/pause` - Pause
- `POST /api/replay/resume` - Resume
- `POST /api/replay/stop` - Stop
- `POST /api/replay/speed` - Set speed
- `POST /api/replay/seek` - Seek by index
- `POST /api/replay/seek-percent` - Seek by %
- `GET /api/replay/status` - Status

### WebSocket (1)
- `WS /ws/observe` - Real-time stream

**Total: 17 endpoints** | **CORS: ✅ Enabled** | **Auth: ❌ None**

---

## 🔗 CORS Configuration

✅ **Enabled for all origins:**
- Allows: `*` (all domains)
- Methods: GET, POST, DELETE, OPTIONS
- Headers: All allowed
- Credentials: Allowed

---

## 📝 Example Request Formats

### Create Alert (Email)
```json
POST http://localhost:8001/api/alerts

{
  "pair": "EURUSD",
  "target_price": 1.0850,
  "condition": "above",
  "channels": ["email"],
  "email": "user@example.com"
}
```

### Create Alert (SMS)
```json
POST http://localhost:8001/api/alerts

{
  "pair": "GOLD",
  "target_price": 2050.50,
  "condition": "below",
  "channels": ["sms"],
  "phone": "+1234567890"
}
```

### Start Replay
```
POST http://localhost:8001/api/replay/start?start_index=0&speed=1.0
```

### Seek Replay
```
POST http://localhost:8001/api/replay/seek?index=50
```

---

## 🧪 WebSocket Testing

### Python (Recommended)
```bash
pip install websockets
# Copy code from WEBSOCKET_TESTING.md
python3 websocket_test.py
```

### Command Line
```bash
# Install websocat: brew install websocat (macOS) or apt-get install websocat (Linux)
websocat ws://localhost:8001/ws/observe
```

### Browser Console
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/observe');
ws.onmessage = e => console.log(JSON.parse(e.data));
```

---

## 📊 WebSocket Message Format

Real-time updates received every 1 second:
```json
{
  "pairs": [
    {"pair": "SPX", "price": "6952.59", "timestamp": "..."},
    {"pair": "GOLD", "price": "2050.50", "timestamp": "..."}
  ],
  "ts": "2026-02-10T12:34:56.789Z",
  "alerts": {
    "active": [...],
    "triggered": [...]
  }
}
```

---

## 📁 Documentation Files

| File | Purpose |
|------|---------|
| `commodities-api.postman_collection.json` | 17 endpoints for Postman |
| `postman-environment.json` | Environment variables |
| `POSTMAN_GUIDE.md` | Detailed setup guide (8.7 KB) |
| `WEBSOCKET_TESTING.md` | WebSocket testing examples (7.3 KB) |
| `BACKEND_API_SUMMARY.md` | Complete implementation summary (11 KB) |

---

## ⚡ Common Commands

```bash
# Start backend
python run.py

# Test API endpoint
curl http://localhost:8001/snapshot

# Test WebSocket
websocat ws://localhost:8001/ws/observe

# Validate Python syntax
python3 -m py_compile main.py

# View API Swagger docs
# Open: http://localhost:8001/docs
```

---

## ✅ Verification Checklist

- ✅ CORS middleware configured in main.py
- ✅ 17 endpoints fully documented
- ✅ Postman collection created (15 endpoints)
- ✅ Environment variables pre-configured
- ✅ WebSocket testing guide included
- ✅ No authentication required
- ✅ All files validated (JSON, Python syntax)

---

## 🎯 Quick Testing Plan

1. **Minute 1-2**: Import Postman collection
2. **Minute 2-3**: Test `/snapshot` endpoint
3. **Minute 3-5**: Create an alert
4. **Minute 5-10**: Test replay endpoints
5. **Minute 10-15**: Connect WebSocket and monitor

**Total time: ~15 minutes** ⏱️

---

## 📞 Support Files

- **POSTMAN_GUIDE.md** - Complete step-by-step guide
- **WEBSOCKET_TESTING.md** - WebSocket examples and troubleshooting
- **BACKEND_API_SUMMARY.md** - Full implementation details

---

**Status**: ✅ **Ready for Testing**

**Next Step**: Start backend server with `python run.py`
