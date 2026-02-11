"""
Replay manager for controlling price data playback.
Handles pause, resume, speed control, and playback status.
"""
import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ReplayState(Enum):
    """States for replay playback."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class ReplayManager:
    """Manages price data replay with speed and timeline control."""

    def __init__(self):
        self.state = ReplayState.STOPPED
        self.current_index: int = 0
        self.total_snapshots: int = 0
        self.speed: float = 1.0  # 0.5x, 1x, 2x, 4x, etc.
        self.start_index: int = 0
        self.end_index: Optional[int] = None
        self.snapshots: list = []

    def start_replay(
        self,
        snapshots: list,
        start_index: int = 0,
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """Start replay from a specific index."""
        if not snapshots:
            raise ValueError("No snapshots provided")

        self.snapshots = snapshots
        self.total_snapshots = len(snapshots)
        self.current_index = start_index
        self.start_index = start_index
        self.end_index = len(snapshots)
        self.speed = max(0.25, min(speed, 4.0))  # Clamp between 0.25x and 4x
        self.state = ReplayState.PLAYING

        logger.info(
            "Started replay: %s snapshots, start=%s, speed=%sx",
            self.total_snapshots,
            start_index,
            self.speed,
        )

        return self.get_status()

    def pause(self) -> Dict[str, Any]:
        """Pause replay."""
        if self.state == ReplayState.PLAYING:
            self.state = ReplayState.PAUSED
            logger.info("Replay paused at snapshot %s/%s", self.current_index, self.total_snapshots)
        return self.get_status()

    def resume(self) -> Dict[str, Any]:
        """Resume replay."""
        if self.state == ReplayState.PAUSED:
            self.state = ReplayState.PLAYING
            logger.info("Replay resumed")
        return self.get_status()

    def stop(self) -> Dict[str, Any]:
        """Stop replay completely."""
        self.state = ReplayState.STOPPED
        self.current_index = 0
        logger.info("Replay stopped")
        return self.get_status()

    def set_speed(self, speed: float) -> Dict[str, Any]:
        """Set replay speed (0.25x to 4x)."""
        self.speed = max(0.25, min(speed, 4.0))
        logger.info("Replay speed set to %sx", self.speed)
        return self.get_status()

    def seek_to_index(self, index: int) -> Dict[str, Any]:
        """Seek to specific snapshot index."""
        if 0 <= index < self.total_snapshots:
            self.current_index = index
            logger.info("Seek to snapshot %s/%s", index, self.total_snapshots)
        return self.get_status()

    def seek_to_percentage(self, percentage: float) -> Dict[str, Any]:
        """Seek to percentage of replay (0-100)."""
        if self.total_snapshots > 0:
            index = int((percentage / 100) * self.total_snapshots)
            self.current_index = min(index, self.total_snapshots - 1)
            logger.info("Seek to %s%% (snapshot %s)", percentage, self.current_index)
        return self.get_status()

    def get_next_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get next snapshot and advance index based on speed."""
        if self.state != ReplayState.PLAYING or not self.snapshots:
            return None

        if self.current_index >= self.total_snapshots:
            # End of replay
            self.state = ReplayState.STOPPED
            return None

        snapshot = self.snapshots[self.current_index]

        # Advance based on speed (1x = 1 snapshot per call)
        # speed > 1 = skip ahead faster
        # speed < 1 = interpolate (stay on same for multiple calls)
        self.current_index += max(1, int(self.speed))

        return snapshot

    def get_status(self) -> Dict[str, Any]:
        """Get current replay status."""
        progress_percent = 0
        if self.total_snapshots > 0:
            progress_percent = (self.current_index / self.total_snapshots) * 100

        return {
            "state": self.state.value,
            "current_index": self.current_index,
            "total_snapshots": self.total_snapshots,
            "progress_percent": round(progress_percent, 2),
            "speed": self.speed,
            "is_playing": self.state == ReplayState.PLAYING,
            "is_paused": self.state == ReplayState.PAUSED,
            "is_stopped": self.state == ReplayState.STOPPED,
        }

    def is_replaying(self) -> bool:
        """Check if replay is currently playing."""
        return self.state == ReplayState.PLAYING
