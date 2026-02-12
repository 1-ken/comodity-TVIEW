from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

METADATA_DIR = BASE_DIR / "metadata"
STORAGE_DIR = BASE_DIR / "storage"
CANDLES_DIR = STORAGE_DIR / "candles"

# Ensure candles directory exists
CANDLES_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = METADATA_DIR / "config.json"
ALERTS_PATH = STORAGE_DIR / "alerts.json"
PRICE_HISTORY_PATH = STORAGE_DIR / "price_history.json"
CANDLES_1M_PATH = CANDLES_DIR / "1m.json"
CANDLES_5M_PATH = CANDLES_DIR / "5m.json"
CANDLES_15M_PATH = CANDLES_DIR / "15m.json"
CANDLES_30M_PATH = CANDLES_DIR / "30m.json"
CANDLES_1H_PATH = CANDLES_DIR / "1h.json"
CANDLES_4H_PATH = CANDLES_DIR / "4h.json"
CANDLES_DAILY_PATH = CANDLES_DIR / "daily.json"
CANDLES_3D_PATH = CANDLES_DIR / "3d.json"
CLIENT_HTML_PATH = BASE_DIR / "client.html"
EXTRACT_PAIRS_HTML_PATH = METADATA_DIR / "toscrap.html"
EXTRACTED_PAIRS_PATH = STORAGE_DIR / "extracted_pairs.json"

CANDLES_PATHS = {
    "1m": CANDLES_1M_PATH,
    "5m": CANDLES_5M_PATH,
    "15m": CANDLES_15M_PATH,
    "30m": CANDLES_30M_PATH,
    "1h": CANDLES_1H_PATH,
    "4h": CANDLES_4H_PATH,
    "daily": CANDLES_DAILY_PATH,
    "3d": CANDLES_3D_PATH,
}
