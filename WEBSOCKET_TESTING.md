#!/usr/bin/env python3
"""
WebSocket Testing Guide for Commodities Observer API

This file contains examples for testing the WebSocket endpoint since Postman's WebSocket support is limited.

Usage:
  1. Start the Commodities Observer backend: python run.py
  2. Run one of the examples below to test real-time streaming
"""

# ============================================================================
# EXAMPLE 1: Python WebSocket Client (Recommended)
# ============================================================================
"""
Install required package:
  pip install websockets

Run the script:
  python websocket_test.py
"""

import asyncio
import websockets
import json
from datetime import datetime


async def test_websocket():
    """Connect to WebSocket and receive real-time price updates."""
    
    # Connection URL
    ws_url = "ws://localhost:8001/ws/observe"
    
    try:
        print(f"Connecting to WebSocket: {ws_url}")
        async with websockets.connect(ws_url) as websocket:
            print("✓ Connected to WebSocket endpoint")
            print("\nReceiving real-time price data (Ctrl+C to stop)...\n")
            
            # Receive messages from the server
            message_count = 0
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    message_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"\n[{timestamp}] Message #{message_count}")
                    print(f"  Timestamp: {data.get('ts', 'N/A')}")
                    
                    # Display pairs
                    pairs = data.get("pairs", [])
                    print(f"  Pairs ({len(pairs)}):")
                    for pair in pairs[:3]:  # Show first 3 pairs
                        print(f"    - {pair.get('pair', 'N/A')}: ${pair.get('price', 'N/A')}")
                    if len(pairs) > 3:
                        print(f"    ... and {len(pairs) - 3} more pairs")
                    
                    # Display alerts
                    alerts = data.get("alerts", {})
                    active_count = len(alerts.get("active", []))
                    triggered_count = len(alerts.get("triggered", []))
                    print(f"  Alerts: {active_count} active, {triggered_count} triggered")
                    
                except asyncio.TimeoutError:
                    print("Connection timeout")
                    break
                except json.JSONDecodeError:
                    print("Failed to parse JSON message")
                    
    except ConnectionRefusedError:
        print("✗ Error: Could not connect to WebSocket server")
        print("  Make sure the server is running: python run.py")
    except asyncio.CancelledError:
        print("\n\nWebSocket connection closed")
    except Exception as e:
        print(f"✗ WebSocket error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\nDisconnected")


# ============================================================================
# EXAMPLE 2: cURL with websocat (Alternative)
# ============================================================================
"""
Install websocat:
  - Ubuntu/Debian: sudo apt-get install websocat
  - macOS: brew install websocat
  - Or use: cargo install websocat

Run:
  websocat ws://localhost:8001/ws/observe

Output will show JSON messages in real-time.
"""


# ============================================================================
# EXAMPLE 3: Node.js WebSocket Client (Alternative)
# ============================================================================
"""
Install required packages:
  npm install ws

Create file: websocket_test.js
"""

node_js_example = '''
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8001/ws/observe');

ws.on('open', function() {
    console.log('Connected to WebSocket endpoint');
});

ws.on('message', function(data) {
    const message = JSON.parse(data);
    console.log('\\n[' + new Date().toLocaleTimeString() + ']');
    console.log('Timestamp:', message.ts);
    
    // Display first 3 pairs
    if (message.pairs && message.pairs.length > 0) {
        console.log('Pairs:');
        message.pairs.slice(0, 3).forEach(pair => {
            console.log(`  ${pair.pair}: $${pair.price}`);
        });
        if (message.pairs.length > 3) {
            console.log(`  ... and ${message.pairs.length - 3} more`);
        }
    }
    
    // Display alerts
    if (message.alerts) {
        console.log('Alerts:', 
            message.alerts.active.length, 'active,',
            message.alerts.triggered.length, 'triggered'
        );
    }
});

ws.on('error', function(error) {
    console.error('WebSocket error:', error);
});

ws.on('close', function() {
    console.log('WebSocket connection closed');
});
'''

# Run with:
# node websocket_test.js


# ============================================================================
# EXAMPLE 4: Browser JavaScript Console (Advanced)
# ============================================================================
"""
Open browser developer console (F12) and paste:

const ws = new WebSocket('ws://localhost:8001/ws/observe');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.clear();
  console.log('Pairs:', data.pairs.slice(0, 3));
  console.log('Alerts:', data.alerts);
};
ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Disconnected');
"""


# ============================================================================
# WEBSOCKET MESSAGE FORMAT
# ============================================================================
"""
Real-time message structure received from /ws/observe:

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
    // ... more pairs
  ],
  "ts": "2026-02-10T12:34:56.789Z",
  "alerts": {
    "active": [
      {
        "id": "uuid-string",
        "pair": "EURUSD",
        "target_price": 1.0850,
        "condition": "above",
        "status": "active",
        "created_at": "2026-02-10T10:00:00Z",
        "channels": ["email", "sms"],
        "email": "user@example.com",
        "phone": "+1234567890",
        "custom_message": "EUR/USD reached target"
      }
    ],
    "triggered": [
      // ... triggered alerts
    ]
  }
}

Broadcast Frequency: Every 1 second (configurable via streamIntervalSeconds in config.json)
"""


# ============================================================================
# TESTING CHECKLIST
# ============================================================================
"""
[ ] WebSocket connects successfully
[ ] Receives messages every 1 second
[ ] Message contains pairs array with prices
[ ] Message includes alerts information
[ ] Messages are valid JSON
[ ] Connection handles disconnect gracefully
[ ] Create an alert via REST API, verify it appears in WebSocket messages
[ ] Trigger an alert, verify it moves to "triggered" list in WebSocket messages
"""
