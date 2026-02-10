# Price Replay System - Documentation

## Overview

The Price Replay System allows you to record live market data and replay it at variable speeds, just like TradingView and other professional charting tools. This is perfect for:

- ✅ **Testing Alerts** - Test your alert strategies with actual market data
- ✅ **Practice Trading** - Practice trading decisions with real historical data  
- ✅ **Debugging Issues** - Replay specific market conditions to debug problems
- ✅ **Sharing Scenarios** - Share exact market conditions with team members
- ✅ **Strategy Backtesting** - Test your trading strategies against recorded data

## Architecture

### Components

1. **price_history.py** - Stores price snapshots in JSON format
2. **replay_manager.py** - Controls playback (play, pause, speed, seek)
3. **main.py** - API endpoints and WebSocket integration
4. **client.html** - Web UI with replay controls

### Data Storage

Price history is stored in `price_history.json` with the following format:

```json
[
  {
    "timestamp": "2026-01-27T19:25:40.782308",
    "snapshot": {
      "title": "AAPL 260.37 ▲ +0.5%",
      "majors": ["SPX", "NDQ", "DJI"],
      "pairs": [
        {"pair": "GOLD", "price": "5,084.88"},
        {"pair": "BTCUSD", "price": "87,759.29"}
      ],
      "alerts": {...}
    }
  }
]
```

## API Endpoints

### Get Replay Information
```bash
GET /api/replay/info
```

Returns total snapshots and date range of available history.

**Response:**
```json
{
  "total_snapshots": 1500,
  "date_range": {
    "start": "2026-01-27T10:00:00",
    "end": "2026-01-27T19:30:00"
  },
  "status": { ... }
}
```

### Start Replay
```bash
POST /api/replay/start?start_index=0&speed=1.0
```

Start replay from a specific snapshot index at given speed.

**Parameters:**
- `start_index` (int): Starting snapshot index (0 = beginning)
- `speed` (float): Playback speed (0.25x to 4x)

**Response:**
```json
{
  "state": "playing",
  "current_index": 0,
  "total_snapshots": 1500,
  "progress_percent": 0.0,
  "speed": 1.0,
  "is_playing": true,
  "is_paused": false,
  "is_stopped": false
}
```

### Control Playback
```bash
POST /api/replay/pause      # Pause playback
POST /api/replay/resume     # Resume from pause
POST /api/replay/stop       # Stop completely
```

### Set Replay Speed
```bash
POST /api/replay/speed?speed=2.0
```

Change playback speed while playing.

**Parameters:**
- `speed` (float): Speed multiplier (0.25x, 0.5x, 1x, 2x, 4x)

### Seek to Index
```bash
POST /api/replay/seek?index=500
```

Jump to specific snapshot index.

### Seek to Percentage
```bash
POST /api/replay/seek-percent?percent=50
```

Jump to percentage of replay (0-100).

### Get Replay Status
```bash
GET /api/replay/status
```

Get current playback status.

### Get Price History
```bash
GET /api/replay/history?limit=100
```

Get recent snapshots from history.

## Web UI Controls

The client interface includes:

### Status Display
- Current playback state (Playing/Paused/Stopped)
- Current snapshot number and total
- Current playback speed

### Progress Bar
- Visual representation of playback progress
- Shows percentage complete

### Timeline Slider
- Drag to seek through replay
- Shows position percentage

### Control Buttons
- **▶ Start Replay** - Begin from start
- **⏸ Pause** - Pause playback
- **▶ Resume** - Resume from pause  
- **⏹ Stop** - Stop completely

### Speed Control
- 0.25x (Super Slow)
- 0.5x (Slow)
- 1x (Normal) - Default
- 2x (Fast)
- 4x (Super Fast)

### History Information
- Total snapshots available
- Date range of recorded data

## Usage Examples

### Example 1: Test Alerts with Historical Data

1. Click "▶ Start Replay"
2. Set speed to 2x to speed through data
3. Watch alerts trigger as prices hit your target levels
4. Check email/SMS notifications

### Example 2: Debug a Specific Market Condition

1. Drag timeline slider to specific time
2. Pause at that point
3. Analyze the market conditions
4. Test your alert sensitivity

### Example 3: Backtest a Trading Strategy

1. Start replay from beginning
2. Watch prices change in real-time
3. Manually record trade signals
4. Review how your alerts performed

## Integration with WebSocket

When replay is active, the WebSocket broadcasts replayed data instead of live data:

```javascript
ws.onmessage = (evt) => {
  const data = JSON.parse(evt.data);
  
  // Access replay status
  const replay = data.replay;
  console.log(replay.state);        // 'playing', 'paused', or 'stopped'
  console.log(replay.speed);        // Current playback speed
  console.log(replay.progress_percent); // 0-100
};
```

## Alert Processing During Replay

When replaying:

1. Historical price data is broadcasted through WebSocket
2. Alerts are checked against replayed prices
3. If alert triggers, notifications are sent immediately
4. Triggered alerts appear in the UI in real-time

This allows you to:
- Test alert accuracy with historical data
- See if you would have caught specific price moves
- Validate alert conditions and tolerances

## Performance Considerations

### Memory Usage
- Each snapshot ~1-2 KB
- 1000 snapshots ~1-2 MB
- Scales linearly with number of snapshots

### Playback Speed
- Can replay 1000s of snapshots quickly
- Speed control prevents CPU overload
- Smooth scrubbing through timeline

## Limitations

1. **Storage**: Data grows over time; consider archiving old data
2. **Accuracy**: Replay shows snapshot data at recording intervals, not every tick
3. **Gaps**: If app restarts, previous history is lost (data in JSON is preserved)

## Future Enhancements

Possible improvements:
- Download/upload replay data
- Multi-file replay concatenation  
- Compressed storage format
- Database backend (SQLite/PostgreSQL)
- Replay export to CSV
- Speed ramping (gradually change speed)
