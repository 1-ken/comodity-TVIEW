from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

METADATA_DIR = BASE_DIR / "metadata"
STORAGE_DIR = BASE_DIR / "storage"

CONFIG_PATH = METADATA_DIR / "config.json"
ALERTS_PATH = STORAGE_DIR / "alerts.json"
PRICE_HISTORY_PATH = STORAGE_DIR / "price_history.json"
CLIENT_HTML_PATH = BASE_DIR / "client.html"
EXTRACT_PAIRS_HTML_PATH = METADATA_DIR / "toscrap.html"
EXTRACTED_PAIRS_PATH = STORAGE_DIR / "extracted_pairs.json"
