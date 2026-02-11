import json
import logging
from typing import Any, Dict

from dotenv import load_dotenv

from app.core.paths import CONFIG_PATH

load_dotenv()

logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Config file not found: %s", CONFIG_PATH)
        raise
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in config file: %s", e)
        raise


CONFIG = load_config()
STREAM_INTERVAL = float(CONFIG.get("streamIntervalSeconds", 1))
SYMBOLS = CONFIG.get("symbols", [])
