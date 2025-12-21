"""
Configuration dataclass for SyncoPaid.

Defines the Config dataclass that holds all application settings
with type annotations and documentation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """
    Application configuration settings.

    Attributes:
        poll_interval_seconds: How often to check the active window (default: 1.0)
        idle_threshold_seconds: Seconds before marking as idle (default: 180)
        merge_threshold_seconds: Max gap to merge identical windows (default: 2.0)
        database_path: Path to SQLite database file (default: auto-detected)
        start_on_boot: Launch automatically on Windows startup (default: False)
        start_tracking_on_launch: Begin tracking when app starts (default: True)
        screenshot_enabled: Enable periodic screenshot capture (default: True)
        screenshot_interval_seconds: Seconds between screenshot attempts (default: 10)
        screenshot_threshold_identical: Similarity threshold to overwrite (≥0.92)
        screenshot_threshold_significant: Similarity threshold for new save (<0.70)
        screenshot_threshold_identical_same_window: Threshold when active window unchanged (default: 0.90)
        screenshot_threshold_identical_different_window: Threshold when active window changed (default: 0.99)
        screenshot_quality: JPEG quality 1-100 (default: 65)
        screenshot_max_dimension: Max width/height in pixels (default: 1920)
        action_screenshot_enabled: Enable action-based screenshot capture (default: True)
        action_screenshot_throttle_seconds: Minimum seconds between action screenshots (default: 0.5)
        action_screenshot_quality: JPEG quality for action screenshots (default: 65)
        action_screenshot_max_dimension: Max dimension for action screenshots (default: 1920)
        minimum_idle_duration_seconds: Minimum idle duration to trigger resumption event (default: 180)
        ui_automation_enabled: Enable UI automation extraction globally (default: True)
        ui_automation_outlook_enabled: Enable UI automation for Outlook (default: True)
        ui_automation_explorer_enabled: Enable UI automation for Explorer (default: True)
    """
    poll_interval_seconds: float = 1.0
    idle_threshold_seconds: float = 180.0
    merge_threshold_seconds: float = 2.0
    database_path: Optional[str] = None
    start_on_boot: bool = False
    start_tracking_on_launch: bool = True
    # Screenshot settings (periodic)
    screenshot_enabled: bool = True
    screenshot_interval_seconds: float = 10.0
    screenshot_threshold_identical: float = 0.92
    screenshot_threshold_significant: float = 0.70
    screenshot_threshold_identical_same_window: float = 0.90
    screenshot_threshold_identical_different_window: float = 0.99
    screenshot_quality: int = 65
    screenshot_max_dimension: int = 1920
    # Action screenshot settings
    action_screenshot_enabled: bool = True
    action_screenshot_throttle_seconds: float = 0.5
    action_screenshot_quality: int = 65
    action_screenshot_max_dimension: int = 1920
    # Idle resumption detection
    minimum_idle_duration_seconds: float = 180
    # UI automation settings
    ui_automation_enabled: bool = True
    ui_automation_outlook_enabled: bool = True
    ui_automation_explorer_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        # Filter only known fields
        valid_fields = {
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        }
        return cls(**valid_fields)
