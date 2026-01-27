# Updated HTML Scraper Configuration

## Summary of Changes

The project has been updated to scrape from a **TradingView-like financial market interface** instead of Yahoo Finance. The new structure extracts **all trading pairs dynamically** across multiple asset classes.

## Key Updates

### 1. **Configuration File** (`config.json`)
Updated selectors to match the new HTML structure:
```json
{
  "url": "https://www.tradingview.com/markets/",
  "waitSelector": ".symbol-RsFlttSS",
  "tableSelector": ".listContainer-MgF6KBas",
  "pairCellSelector": ".symbol-RsFlttSS",
  "symbolNameSelector": ".symbolNameText-RsFlttSS",
  "priceSelector": ".last-RsFlttSS .inner-RsFlttSS",
  "symbols": [],
  "streamIntervalSeconds": 1
}
```

**Key Changes:**
- `tableSelector`: Changed from `"table"` to `.listContainer-MgF6KBas` (uses div containers instead of HTML tables)
- `pairCellSelector`: Changed to `.symbol-RsFlttSS` (TradingView uses div-based structure)
- `symbolNameSelector`: New selector for extracting pair names (`.symbolNameText-RsFlttSS`)
- `priceSelector`: New selector for extracting prices (`.last-RsFlttSS .inner-RsFlttSS`)
- `symbols`: Now empty array - pairs are discovered dynamically

### 2. **Observer Module** (`observer.py`)
Updated the `snapshot()` method to:
- Use `.query_selector_all(".symbol-RsFlttSS")` to find all pair elements
- Extract pair names from `.symbolNameText-RsFlttSS` 
- Extract prices from `.last-RsFlttSS .inner-RsFlttSS`
- Handle multi-line price formatting (removes whitespace)
- Include error handling for network/page load issues

### 3. **New Extraction Script** (`extract_pairs.py`)
A utility script that demonstrates how to:
- Parse the HTML structure to extract all pairs
- Categorize pairs by their section (Indices, Stocks, Futures, Forex, Crypto)
- Save extracted data to JSON

## HTML Structure

The new structure uses:
```html
<div class="symbol-RsFlttSS">
  <div class="firstItem-RsFlttSS symbolName-RsFlttSS">
    <span class="symbolNameText-RsFlttSS">PAIR_NAME</span>
  </div>
  <span class="cell-RsFlttSS last-RsFlttSS">
    <span class="inner-RsFlttSS">PRICE</span>
  </span>
</div>
```

## Extracted Data Format

The scraper now extracts pairs in this format:
```json
{
  "Indices": [
    {"pair": "SPX", "price": "6,952.59"},
    {"pair": "NDQ", "price": "25,738.02"},
    ...
  ],
  "Stocks": [
    {"pair": "AAPL", "price": "255.22"},
    ...
  ],
  "Futures": [...],
  "Forex": [...],
  "Crypto": [...]
}
```

## Supported Asset Classes

The scraper now automatically extracts and categorizes:

1. **Indices** (5+): SPX, NDQ, DJI, VIX, DXY
2. **Stocks** (3+): AAPL, TSLA, NFLX
3. **Futures** (3+): USOIL, GOLD, SILVER
4. **Forex** (3+): EURUSD, GBPUSD, USDJPY
5. **Crypto** (3+): BTCUSD, BTCUSDT, ETHUSD

## Running the Scraper

### Extract Static Data from HTML
```bash
python3 extract_pairs.py
```

Output:
```
✓ Successfully extracted 17 pairs from 5 categories

📊 Indices (5 pairs):
   1. SPX          → 6,952.59
   2. NDQ          → 25,738.02
   ...

✓ Extracted data saved to extracted_pairs.json
```

### Run the Full Application
```bash
python run.py
```

The application will:
- Start a FastAPI server on `http://0.0.0.0:8001`
- Monitor the configured URL for price updates
- Stream real-time data via WebSocket
- Trigger alerts when prices reach specified thresholds

## API Endpoints

- `GET /` - Serve client HTML
- `GET /snapshot` - Get current market snapshot
- `GET /client-config` - Get WebSocket configuration
- `WebSocket /ws/observe` - Stream real-time data
- `POST /api/alerts` - Create price alert
- `GET /api/alerts` - List all alerts
- `GET /api/alerts/{id}` - Get specific alert
- `DELETE /api/alerts/{id}` - Delete alert

## Alert Features

The application supports:
- Price thresholds: `above`, `below`, `equal`
- Multiple notification channels: `email` (SendGrid), `SMS` (Africa's Talking)
- Custom alert messages
- Automatic trigger detection and logging

## Testing

To verify the installation works:
```bash
python3 -m py_compile observer.py alerts.py main.py
```

## Fixed Issues

✅ Fixed AttributeError in alerts.py when loading empty alerts.json (handles both list and dict formats)
✅ Updated HTML selectors for TradingView-like structure
✅ Implemented dynamic pair discovery (no hardcoded symbols list needed)
✅ Added proper error handling for modern JavaScript-heavy websites
