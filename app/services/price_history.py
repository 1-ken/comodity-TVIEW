"""
Price history storage and management for replay functionality.
Stores price snapshots with timestamps in JSON format.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.core.paths import PRICE_HISTORY_PATH

logger = logging.getLogger(__name__)

PRICE_HISTORY_FILE = str(PRICE_HISTORY_PATH)


class PriceHistory:
    """Manages historical price data for replay."""

    def __init__(self, file_path: str = PRICE_HISTORY_FILE):
        self.file_path = file_path
        self.history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load price history from file."""
        try:
            if Path(self.file_path).exists():
                with open(self.file_path, "r") as f:
                    self.history = json.load(f)
                logger.info("Loaded %s historical snapshots", len(self.history))
            else:
                logger.info("No existing price history file, starting fresh")
                self.history = []
        except Exception as e:
            logger.error("Error loading price history: %s", e)
            self.history = []

    def _save_history(self) -> None:
        """Save price history to file."""
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error("Error saving price history: %s", e)

    def add_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Add a price snapshot with timestamp."""
        # Remove 'ts' field if it exists and add it at our chosen location
        snapshot_copy = {k: v for k, v in snapshot.items() if k != "ts"}
        timestamp = snapshot.get("ts") or datetime.now().isoformat()

        historical_entry = {
            "timestamp": timestamp,
            "snapshot": snapshot_copy,
        }
        self.history.append(historical_entry)
        self._save_history()

    def get_history_range(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical snapshots within a time range."""
        if not start_time and not end_time:
            return self.history

        filtered = []
        for entry in self.history:
            ts = entry.get("timestamp", "")
            if start_time and ts < start_time:
                continue
            if end_time and ts > end_time:
                continue
            filtered.append(entry)
        return filtered

    def get_snapshot_at_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get snapshot at specific index."""
        if 0 <= index < len(self.history):
            return self.history[index]
        return None

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot."""
        return self.history[-1] if self.history else None

    def get_snapshot_count(self) -> int:
        """Get total number of snapshots."""
        return len(self.history)

    def clear_history(self) -> None:
        """Clear all history (use with caution)."""
        logger.warning("Clearing all price history")
        self.history = []
        self._save_history()

    def get_date_range(self) -> Optional[Dict[str, str]]:
        """Get earliest and latest timestamp in history."""
        if not self.history:
            return None
        return {
            "start": self.history[0].get("timestamp"),
            "end": self.history[-1].get("timestamp"),
        }
