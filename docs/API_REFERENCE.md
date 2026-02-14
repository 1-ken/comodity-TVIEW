# Commodities API Reference

Complete API documentation for the Commodities Observer application with request and response examples.

## Base URL

```
http://localhost:8001/api
```

## WebSocket URL

```
ws://localhost:8001/ws/observe
```

---

## Table of Contents

- [Public Endpoints](#public-endpoints)
- [Candles API](#candles-api)
- [Alerts API](#alerts-api)
- [Replay API](#replay-api)
- [WebSocket Streaming](#websocket-streaming)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)

---

## Public Endpoints

### Get Client Configuration

Retrieve runtime configuration for the client application.

**Endpoint:** `GET /client-config`

**Request:**

```bash
curl http://localhost:8001/client-config
```

**Response (200 OK):**

```json
{
  "wsUrl": "ws://localhost:8001/ws/observe"
}
```

---

### Get Snapshot

Get a single snapshot of current commodities data.

**Endpoint:** `GET /snapshot`

**Request:**

```bash
curl http://localhost:8001/snapshot
```

**Response (200 OK):**

```json
{
  "title": "Commodities Market Data",
  "majors": ["USD", "EUR"],
  "pairs": [
    {
      "pair": "GOLD",
      "price": "2049.90",
      "change": "+0.25%"
    },
    {
      "pair": "BTCUSD",
      "price": "68987.50",
      "change": "-1.2%"
    }
  ],
  "pairsSample": ["GOLD", "BTCUSD", "ETHUSD"],
  "changes": ["+0.25%", "-1.2%"],
  "ts": "2026-02-14T06:35:27.123456"
}
```

---

## Candles API

OHLC (Open, High, Low, Close) candlestick data across multiple timeframes.

### Get Available Timeframes

**Endpoint:** `GET /api/candles/available-timeframes`

**Request:**

```bash
curl http://localhost:8001/api/candles/available-timeframes
```

**Response (200 OK):**

```json
{
  "timeframes": [
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "daily",
    "3d"
  ],
  "descriptions": {
    "1m": "1-minute candles",
    "5m": "5-minute candles",
    "15m": "15-minute candles",
    "30m": "30-minute candles",
    "1h": "1-hour candles",
    "4h": "4-hour candles",
    "daily": "Daily candles",
    "3d": "3-day candles"
  }
}
```

---

### Get Candles by Timeframe

Retrieve OHLC candles for a specific timeframe.

**Endpoint:** `GET /api/candles/{timeframe}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeframe` | string | Timeframe: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `daily`, `3d` |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Number of candles to retrieve |
| `pair` | string | null | Optional: Filter by specific trading pair (e.g., `GOLD`, `BTCUSD`) |

**Request:**

```bash
# Get last 100 candles for 1-hour timeframe
curl http://localhost:8001/api/candles/1h?limit=100

# Get last 50 candles for 1-minute timeframe, filtered by BTCUSD
curl http://localhost:8001/api/candles/1m?limit=50&pair=BTCUSD

# Get daily candles
curl http://localhost:8001/api/candles/daily?limit=30
```

**Response (200 OK):**

```json
{
  "timeframe": "1h",
  "pair": "all",
  "count": 5,
  "candles": [
    {
      "id": 6577546,
      "pair": "EURUSD",
      "timeframe": "1h",
      "timestamp": "2026-02-14T06:00:00",
      "open": 1.36514,
      "high": 1.36514,
      "low": 1.36514,
      "close": 1.36514,
      "volume": 239.0
    },
    {
      "id": 6577862,
      "pair": "GOLD",
      "timeframe": "1h",
      "timestamp": "2026-02-14T06:00:00",
      "open": 152.629,
      "high": 152.629,
      "low": 152.629,
      "close": 152.629,
      "volume": 239.0
    },
    {
      "id": 6578178,
      "pair": "BTCUSD",
      "timeframe": "1h",
      "timestamp": "2026-02-14T06:00:00",
      "open": 68852.0,
      "high": 68944.0,
      "low": 68817.0,
      "close": 68944.0,
      "volume": 239.0
    }
  ]
}
```

---

### Get Latest Candle

Retrieve the most recent candle for a specific timeframe.

**Endpoint:** `GET /api/candles/{timeframe}/latest`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeframe` | string | Timeframe: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `daily`, `3d` |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pair` | string | Optional: Specific trading pair |

**Request:**

```bash
# Get latest 1-hour candle
curl http://localhost:8001/api/candles/1h/latest

# Get latest 1-minute candle for GOLD
curl http://localhost:8001/api/candles/1m/latest?pair=GOLD
```

**Response (200 OK):**

```json
{
  "timeframe": "1h",
  "candle": {
    "id": 6578810,
    "pair": "GOLD",
    "timeframe": "1h",
    "timestamp": "2026-02-14T07:00:00",
    "open": 2049.9,
    "high": 2052.5,
    "low": 2047.4,
    "close": 2052.5,
    "volume": 239.0
  }
}
```

**Response (200 OK - No Data):**

```json
{
  "timeframe": "1m",
  "pair": "BTCUSD",
  "candle": null,
  "message": "No candles for pair BTCUSD"
}
```

---

### Get Candles by Date Range

Retrieve candles within a specific date range.

**Endpoint:** `GET /api/candles/{timeframe}/range`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeframe` | string | Timeframe: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `daily`, `3d` |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | **Required.** ISO format: `2026-02-01T00:00:00` |
| `end_date` | string | **Required.** ISO format: `2026-02-14T23:59:59` |
| `pair` | string | Optional: Filter by specific trading pair |

**Request:**

```bash
# Get daily candles for February 2026
curl "http://localhost:8001/api/candles/daily/range?start_date=2026-02-01T00:00:00&end_date=2026-02-28T23:59:59"

# Get 1-hour candles for a specific date range filtered by GOLD
curl "http://localhost:8001/api/candles/1h/range?start_date=2026-02-10T00:00:00&end_date=2026-02-14T23:59:59&pair=GOLD"
```

**Response (200 OK):**

```json
{
  "timeframe": "daily",
  "pair": "all",
  "start_date": "2026-02-01T00:00:00",
  "end_date": "2026-02-28T23:59:59",
  "count": 14,
  "candles": [
    {
      "id": 1001,
      "pair": "GOLD",
      "timeframe": "daily",
      "timestamp": "2026-02-01T00:00:00",
      "open": 2045.10,
      "high": 2052.50,
      "low": 2043.00,
      "close": 2050.25,
      "volume": 5000.0
    }
  ]
}
```

---

### Get Candle Statistics

Get statistics about stored candles across all timeframes.

**Endpoint:** `GET /api/candles/stats`

**Request:**

```bash
curl http://localhost:8001/api/candles/stats
```

**Response (200 OK):**

```json
{
  "total_candles": 15,
  "by_timeframe": {
    "1m": 0,
    "5m": 0,
    "15m": 0,
    "30m": 0,
    "1h": 5,
    "4h": 0,
    "daily": 10,
    "3d": 0
  }
}
```

---

### Regenerate Candles

Regenerate OHLC candles from price history for a specific timeframe.

**Endpoint:** `POST /api/candles/{timeframe}/regenerate`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeframe` | string | Timeframe: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `daily`, `3d` |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `pair` | string | Optional: Specific trading pair to regenerate |

**Request:**

```bash
# Regenerate 1-hour candles for all pairs
curl -X POST http://localhost:8001/api/candles/1h/regenerate

# Regenerate daily candles for GOLD only
curl -X POST "http://localhost:8001/api/candles/daily/regenerate?pair=GOLD"
```

**Response (200 OK):**

```json
{
  "success": true,
  "timeframe": "1h",
  "candles_generated": 150,
  "message": "Candles regenerated successfully"
}
```

---

## Alerts API

Create and manage price alerts for trading pairs.

### Create Alert

Create a new price alert with notification channels.

**Endpoint:** `POST /api/alerts`

**Request Body:**

```json
{
  "pair": "GOLD",
  "target_price": 2050.0,
  "condition": "above",
  "channels": ["email", "sms"],
  "email": "user@example.com",
  "phone": "+1234567890",
  "custom_message": "Gold price exceeded target!"
}
```

**Request:**

```bash
curl -X POST http://localhost:8001/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "BTCUSD",
    "target_price": 70000,
    "condition": "above",
    "channels": ["email"],
    "email": "trader@example.com"
  }'
```

**Response (200 OK):**

```json
{
  "success": true,
  "alert": {
    "id": "alert_1708953327",
    "pair": "BTCUSD",
    "target_price": 70000.0,
    "condition": "above",
    "channels": ["email"],
    "email": "trader@example.com",
    "phone": "",
    "custom_message": "",
    "status": "active",
    "created_at": "2026-02-14T06:35:27"
  }
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Condition must be 'above', 'below', or 'equal'"
}
```

---

### Get All Alerts

Retrieve all alerts organized by status.

**Endpoint:** `GET /api/alerts`

**Request:**

```bash
curl http://localhost:8001/api/alerts
```

**Response (200 OK):**

```json
{
  "total": 3,
  "active": [
    {
      "id": "alert_1708953327",
      "pair": "BTCUSD",
      "target_price": 70000.0,
      "condition": "above",
      "channels": ["email"],
      "status": "active",
      "created_at": "2026-02-14T06:35:27"
    }
  ],
  "triggered": [
    {
      "id": "alert_1708953200",
      "pair": "GOLD",
      "target_price": 2050.0,
      "condition": "below",
      "channels": ["sms"],
      "status": "triggered",
      "created_at": "2026-02-14T05:00:00"
    }
  ],
  "all": []
}
```

---

### Get Specific Alert

Retrieve details for a specific alert by ID.

**Endpoint:** `GET /api/alerts/{alert_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `alert_id` | string | Alert ID returned from create alert endpoint |

**Request:**

```bash
curl http://localhost:8001/api/alerts/alert_1708953327
```

**Response (200 OK):**

```json
{
  "id": "alert_1708953327",
  "pair": "BTCUSD",
  "target_price": 70000.0,
  "condition": "above",
  "channels": ["email"],
  "email": "trader@example.com",
  "phone": "",
  "custom_message": "",
  "status": "active",
  "created_at": "2026-02-14T06:35:27"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Alert not found"
}
```

---

### Delete Alert

Delete an alert by ID.

**Endpoint:** `DELETE /api/alerts/{alert_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `alert_id` | string | Alert ID to delete |

**Request:**

```bash
curl -X DELETE http://localhost:8001/api/alerts/alert_1708953327
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Alert deleted"
}
```

**Response (404 Not Found):**

```json
{
  "detail": "Alert not found"
}
```

---

## Replay API

Control and manage price data replay for backtesting and historical analysis.

### Get Replay Info

Get information about available price history and replay status.

**Endpoint:** `GET /api/replay/info`

**Request:**

```bash
curl http://localhost:8001/api/replay/info
```

**Response (200 OK):**

```json
{
  "total_snapshots": 1500,
  "date_range": {
    "start": "2026-01-01T00:00:00",
    "end": "2026-02-14T23:59:59"
  },
  "status": {
    "is_running": false,
    "current_index": 0,
    "speed": 1.0
  }
}
```

---

### Start Replay

Start price data replay from a specific point.

**Endpoint:** `POST /api/replay/start`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_index` | integer | 0 | Starting snapshot index (0 to total_snapshots-1) |
| `speed` | float | 1.0 | Replay speed (0.25x to 4.0x) |

**Request:**

```bash
# Start replay from beginning at normal speed
curl -X POST http://localhost:8001/api/replay/start

# Start from index 500 at 2x speed
curl -X POST "http://localhost:8001/api/replay/start?start_index=500&speed=2.0"
```

**Response (200 OK):**

```json
{
  "is_running": true,
  "current_index": 0,
  "speed": 1.0,
  "total_snapshots": 1500,
  "message": "Replay started"
}
```

**Response (400 Bad Request):**

```json
{
  "detail": "Speed must be between 0.25 and 4.0"
}
```

---

### Pause Replay

Pause the ongoing replay.

**Endpoint:** `POST /api/replay/pause`

**Request:**

```bash
curl -X POST http://localhost:8001/api/replay/pause
```

**Response (200 OK):**

```json
{
  "is_running": false,
  "current_index": 750,
  "speed": 1.0,
  "message": "Replay paused"
}
```

---

### Resume Replay

Resume a paused replay.

**Endpoint:** `POST /api/replay/resume`

**Request:**

```bash
curl -X POST http://localhost:8001/api/replay/resume
```

**Response (200 OK):**

```json
{
  "is_running": true,
  "current_index": 750,
  "speed": 1.0,
  "message": "Replay resumed"
}
```

---

## WebSocket Streaming

Real-time streaming of commodities data via WebSocket connection.

### Subscribe to Real-Time Data

Connect to stream real-time commodities price updates.

**Endpoint:** `ws://localhost:8001/ws/observe`

**JavaScript Example:**

```javascript
const ws = new WebSocket("ws://localhost:8001/ws/observe");

ws.onopen = (event) => {
  console.log("Connected to WebSocket");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received update:", data);
  // data structure matches GET /snapshot response
};

ws.onerror = (event) => {
  console.error("WebSocket error:", event);
};

ws.onclose = (event) => {
  console.log("WebSocket closed");
};
```

**Python Example (using websockets library):**

```python
import asyncio
import json
import websockets

async def stream_data():
    uri = "ws://localhost:8001/ws/observe"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            message = json.loads(data)
            print("Received:", message)

asyncio.run(stream_data())
```

**Message Format:**

Same as `/snapshot` endpoint - contains real-time commodities data with pairs and prices.

```json
{
  "title": "Commodities Market Data",
  "majors": ["USD", "EUR"],
  "pairs": [
    {
      "pair": "GOLD",
      "price": "2049.90",
      "change": "+0.25%"
    }
  ],
  "ts": "2026-02-14T06:35:27.123456"
}
```

---

## Response Formats

### Success Response

All successful API responses follow this general structure:

```json
{
  "success": true,
  "data": {},
  "message": "Optional message"
}
```

### Error Response

All error responses include an HTTP status code and error details:

```json
{
  "detail": "Error description"
}
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid parameters or missing required fields |
| 404 | Not Found | Resource (alert, candle) not found |
| 503 | Service Unavailable | Observer not ready or database offline |
| 500 | Internal Server Error | Unexpected server error |

### Error Response Examples

**400 - Bad Request:**

```json
{
  "detail": "Condition must be 'above', 'below', or 'equal'"
}
```

**404 - Not Found:**

```json
{
  "detail": "Alert not found"
}
```

**503 - Service Unavailable:**

```json
{
  "error": "Observer not ready"
}
```

---

## Rate Limiting & Best Practices

- No strict rate limiting is currently implemented, but avoid excessive polling
- For real-time data, use the WebSocket connection instead of polling HTTP endpoints
- Cache responses when possible to reduce server load
- Use appropriate query parameters (`limit`, `pair`, `start_date`, `end_date`) to reduce payload size

---

## Examples

### Complete Workflow Example

```bash
# 1. Get available timeframes
curl http://localhost:8001/api/candles/available-timeframes

# 2. Get current snapshot
curl http://localhost:8001/snapshot

# 3. Create a price alert
curl -X POST http://localhost:8001/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "GOLD",
    "target_price": 2050,
    "condition": "above",
    "channels": ["email"],
    "email": "user@example.com"
  }'

# 4. Get alert details
curl http://localhost:8001/api/alerts/alert_1708953327

# 5. Get recent 1-hour candles
curl http://localhost:8001/api/candles/1h?limit=50

# 6. Get candles for date range
curl "http://localhost:8001/api/candles/daily/range?start_date=2026-02-01T00:00:00&end_date=2026-02-14T23:59:59"
```

---

## Support & Documentation

For more information:
- See [START_HERE.md](START_HERE.md) for setup instructions
- See [BACKEND_API_SUMMARY.md](BACKEND_API_SUMMARY.md) for internal architecture
- Check Postman collections in `docs/` folder for pre-built requests
