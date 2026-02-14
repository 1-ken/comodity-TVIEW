# Postman Collection Guide - Commodities Observer v2

## Overview
Complete Postman collection for testing all Commodities Observer APIs with PostgreSQL backend.

## Files
- **`commodities-api-v2.postman_collection.json`** - Main collection (27 requests)
- **`commodities-environment-v2.postman_environment.json`** - Environment variables

## Quick Setup

### 1. Import Collection
1. Open Postman
2. Click **Import** button
3. Select both files:
   - `commodities-api-v2.postman_collection.json`
   - `commodities-environment-v2.postman_environment.json`
4. Click **Import**

### 2. Select Environment
1. Click environment dropdown (top right)
2. Select **"Commodities Observer - PostgreSQL v2"**

### 3. Start Application
```bash
cd /home/here/Desktop/prompts/commodities
source .venv/bin/activate
python run.py
```

## Collection Structure

### 📁 Public Endpoints (3 requests)
- **GET /** - Client HTML interface
- **GET /snapshot** - Current price snapshot
- **GET /client-config** - WebSocket configuration

### 📁 Alerts (6 requests)
- **POST /api/alerts** - Create alert (Email, SMS, or Both)
- **GET /api/alerts** - Get all alerts
- **GET /api/alerts/{id}** - Get specific alert
- **DELETE /api/alerts/{id}** - Delete alert

### 📁 Replay (10 requests)
- **GET /api/replay/info** - Replay information
- **GET /api/replay/status** - Current replay status
- **GET /api/replay/history** - Price history snapshots
- **POST /api/replay/start** - Start replay
- **POST /api/replay/pause** - Pause replay
- **POST /api/replay/resume** - Resume replay
- **POST /api/replay/stop** - Stop replay
- **POST /api/replay/speed** - Change speed
- **POST /api/replay/seek** - Seek to index
- **POST /api/replay/seek-percent** - Seek to percentage

### 📁 Candles (7 requests)
- **GET /api/candles/available-timeframes** - List timeframes
- **GET /api/candles/{timeframe}** - Get candles
- **GET /api/candles/{timeframe}/latest** - Latest candle
- **GET /api/candles/{timeframe}/range** - Date range query
- **GET /api/candles/stats** - Candle statistics
- **POST /api/candles/{timeframe}/regenerate** - Regenerate candles

### 📁 WebSocket (1 request)
- WebSocket connection info

## Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | http://localhost:8001 | API base URL |
| `ws_url` | ws://localhost:8001/ws/observe | WebSocket URL |
| `alert_id` | (empty) | Alert UUID for testing |
| `email` | test@example.com | Email for alerts |
| `phone` | +1234567890 | Phone for SMS alerts |
| `test_pair` | GOLD | Trading pair for testing |
| `test_target_price` | 5100 | Target price for alerts |

## Usage Examples

### Create an Alert
1. Select **Alerts** → **Create Alert - Email**
2. Modify the body if needed:
   ```json
   {
     "pair": "GOLD",
     "target_price": 5100,
     "condition": "above",
     "channels": ["email"],
     "email": "your@email.com",
     "custom_message": "Gold alert!"
   }
   ```
3. Click **Send**
4. Copy the `alert_id` from response
5. Update environment variable `alert_id` with the copied value

### Test Replay
1. Get info: **Replay** → **Get Replay Info**
2. Start replay: **Replay** → **Start Replay** (adjust speed parameter)
3. Check status: **Replay** → **Get Replay Status**
4. Pause/Resume as needed
5. Stop when done: **Replay** → **Stop Replay**

### Query Candles
1. Get available timeframes: **Candles** → **Get Available Timeframes**
2. Get candles: **Candles** → **Get Candles - Specific Pair**
   - Modify URL: `/api/candles/1m?limit=50&pair=BTCUSD`
3. Get statistics: **Candles** → **Get Candle Stats**

## Alert Conditions

| Condition | Description | Example |
|-----------|-------------|---------|
| `above` | Price goes above target | Price > 5100 |
| `below` | Price goes below target | Price < 5000 |
| `equal` | Price equals target (±tolerance) | Price ≈ 5050 |

## Replay Speed Options

- **0.25x** - Slow motion (4x slower)
- **0.5x** - Half speed (2x slower)
- **1.0x** - Normal speed
- **2.0x** - Double speed
- **4.0x** - Fast forward (4x faster)

## Candle Timeframes

| Timeframe | Description |
|-----------|-------------|
| `1m` | 1-minute candles |
| `5m` | 5-minute candles |
| `15m` | 15-minute candles |
| `30m` | 30-minute candles |
| `1h` | 1-hour candles |
| `4h` | 4-hour candles |
| `daily` | Daily candles |
| `3d` | 3-day candles |

## Testing Workflow

### Complete Test Run (5 minutes)

1. **Test Public Endpoints**
   ```
   GET /snapshot → Verify price data
   GET /client-config → Check WebSocket URL
   ```

2. **Test Alerts**
   ```
   POST /api/alerts → Create new alert
   GET /api/alerts → Verify creation
   GET /api/alerts/{id} → Get specific alert
   DELETE /api/alerts/{id} → Clean up
   ```

3. **Test Replay**
   ```
   GET /api/replay/info → Check available data
   POST /api/replay/start → Start at speed 2.0
   GET /api/replay/status → Verify running
   POST /api/replay/pause → Pause
   POST /api/replay/resume → Resume
   POST /api/replay/stop → Stop
   ```

4. **Test Candles**
   ```
   GET /api/candles/available-timeframes → List all
   GET /api/candles/1h?limit=10 → Get 10 candles
   GET /api/candles/1h/latest → Latest candle
   GET /api/candles/stats → Statistics
   ```

## Tips

### Save Alert ID
After creating an alert, save its ID to the environment:
1. Copy `id` from response
2. Go to **Environments** → **Commodities Observer - PostgreSQL v2**
3. Set `alert_id` value
4. Save

### Change Base URL
To test against a different server:
1. Edit environment variable `base_url`
2. Example: `http://192.168.1.100:8001`

### Test with Real Data
1. Let app run for a few minutes to collect data
2. Check replay history: `GET /api/replay/history`
3. Query candles: `GET /api/candles/stats`

## WebSocket Testing

The collection includes WebSocket info, but for WebSocket testing use:

**URL:** `ws://localhost:8001/ws/observe`

**Tools:**
- [wscat](https://github.com/websockets/wscat): `wscat -c ws://localhost:8001/ws/observe`
- [Postman WebSocket](https://learning.postman.com/docs/sending-requests/websocket/websocket/)
- Browser DevTools

## Troubleshooting

### Error: Connection refused
```
Application is not running. Start it:
python run.py
```

### Error: 404 Not Found
```
Check URL path. All API endpoints start with /api except:
- /snapshot
- /client-config
- /
```

### Error: 500 Internal Server Error
```
Check application logs:
tail -f /tmp/test_app.log
```

### Empty Response
```
Wait for app to collect data (30 seconds)
Check GET /snapshot for live data
```

## PostgreSQL Verification

After testing, verify data in database:

```bash
PGPASSWORD=mypassword psql -h localhost -U myuser -d commodities

# View alerts
SELECT id, pair, target_price, status FROM alerts;

# View candle counts
SELECT timeframe, COUNT(*) FROM candles GROUP BY timeframe;

# View price history
SELECT COUNT(*) FROM price_history;
```

## Additional Resources

- API Documentation: [BACKEND_API_SUMMARY.md](BACKEND_API_SUMMARY.md)
- PostgreSQL Guide: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)
- Quick Reference: [POSTGRESQL_QUICK_REFERENCE.md](POSTGRESQL_QUICK_REFERENCE.md)

## Collection Stats

- **Total Requests:** 27
- **Folders:** 5
- **Environment Variables:** 7
- **Supported Methods:** GET, POST, DELETE

---

**Version:** 2.0 (PostgreSQL)
**Last Updated:** February 12, 2026
**Base URL:** http://localhost:8001
