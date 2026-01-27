# Commodities Observer

Real-time commodities price monitoring with price alerts.

## Overview

This is an independent project that monitors commodity prices from Yahoo Finance and provides real-time price alerts via email or SMS.

## Features

- **Real-time Price Monitoring**: Live streaming of commodity prices via WebSocket
- **Price Alerts**: Set alerts for price thresholds (above, below, or equal to target prices)
- **Multiple Notification Channels**: Receive alerts via email (SendGrid) or SMS (Africa's Talking)
- **Custom Alert Messages**: Add personalized messages to your alerts
- **Web Interface**: Clean, intuitive UI for monitoring and managing alerts

## Tracked Commodities

- **GC=F** - Gold Futures
- **SI=F** - Silver Futures
- **CL=F** - Crude Oil
- **NG=F** - Natural Gas
- **HG=F** - Copper
- **PL=F** - Platinum
- **PA=F** - Palladium
- **ZC=F** - Corn
- **ZS=F** - Soybeans
- **KC=F** - Coffee

## Installation

### Prerequisites

- Python 3.13+
- SendGrid API key (for email alerts)
- Africa's Talking credentials (for SMS alerts)

### Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate  # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure environment variables:**
   
   Edit the `.env` file with your credentials:
   ```env
   SENDGRID_API_KEY=your_sendgrid_api_key
   FROM_EMAIL=your_email@domain.com
   AFRICASTALKING_USERNAME=your_at_username
   AFRICASTALKING_API_KEY=your_at_api_key
   WS_URL=ws://localhost:8001/ws/observe
   ```

4. **Configure commodities (optional):**
   
   Edit `config.json` to customize tracked commodities and scraping parameters.

## Running the Application

### Development Mode

```bash
python run.py
```

The application will start on `http://localhost:8001`

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Usage

1. **Access the web interface**: Open `http://localhost:8001` in your browser

2. **Monitor real-time prices**: The dashboard displays live commodity prices

3. **Create price alerts**:
   - Select a commodity from the dropdown
   - Enter target price
   - Choose condition (above/below/equal)
   - Select notification channel (email or SMS)
   - Enter contact details
   - Optionally add a custom message

4. **Manage alerts**: View active and triggered alerts in the dashboard

## API Endpoints

- `GET /` - Web interface
- `GET /client-config` - Client configuration
- `GET /snapshot` - Single snapshot of current prices
- `WS /ws/observe` - WebSocket for real-time price streaming
- `POST /api/alerts` - Create a new alert
- `GET /api/alerts` - Get all alerts
- `GET /api/alerts/{alert_id}` - Get specific alert
- `DELETE /api/alerts/{alert_id}` - Delete an alert

## Configuration

### config.json

```json
{
  "url": "https://finance.yahoo.com/markets/commodities/",
  "waitSelector": "table tbody tr",
  "tableSelector": "table",
  "pairCellSelector": "tbody tr td:first-child .symbol",
  "priceIndex": 3,
  "streamIntervalSeconds": 0.2,
  "symbols": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "PL=F", "PA=F", "ZC=F", "ZS=F", "KC=F"],
  "injectMutationObserver": true
}
```

- **url**: Yahoo Finance commodities page URL
- **streamIntervalSeconds**: How often to check for price updates (in seconds)
- **symbols**: List of commodity symbols to track
- **priceIndex**: Column index containing price data
- **pairCellSelector**: CSS selector for commodity symbol cells
- **tableSelector**: CSS selector for the price table

## Project Structure

```
commodities/
├── main.py              # FastAPI application
├── observer.py          # Web scraper using Playwright
├── alerts.py            # Alert management system
├── email_service.py     # Email notifications via SendGrid
├── sms_service.py       # SMS notifications via Africa's Talking
├── client.html          # Web interface
├── config.json          # Configuration file
├── alerts.json          # Persisted alerts data
├── .env                 # Environment variables (not in git)
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata
├── runtime.txt          # Python version
├── run.py               # Entry point script
└── README.md            # This file
```

## Troubleshooting

### WebSocket Connection Issues

If you can't connect to the WebSocket:
- Check that the server is running on port 8001
- Verify firewall settings allow connections on port 8001
- Check browser console for error messages

### No Price Data

If prices aren't updating:
- Verify internet connection
- Check if Yahoo Finance structure has changed
- Review server logs for scraping errors
- Ensure Playwright/Chromium is properly installed

### Alerts Not Triggering

If alerts aren't firing:
- Verify SendGrid/Africa's Talking credentials in `.env`
- Check `alerts.json` for correct alert configuration
- Review server logs for notification errors

## License

This project is for educational and personal use only.
