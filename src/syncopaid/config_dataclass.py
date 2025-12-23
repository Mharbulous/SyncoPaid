"""
Configuration dataclass for SyncoPaid.

Defines the Config dataclass that holds all application settings
with type annotations and documentation.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field


# Validation constants
IDLE_THRESHOLD_MIN = 10.0
IDLE_THRESHOLD_MAX = 600.0
IDLE_THRESHOLD_DEFAULT = 180.0


def validate_idle_threshold(value: float) -> float:
    """
    Validate idle_threshold_seconds value.

    Args:
        value: The idle threshold value to validate

    Returns:
        The validated value, or default if invalid

    Valid range: 10-600 seconds (10 seconds to 10 minutes)
    Invalid values log a warning and return the default (180s).
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        logging.warning(
            f"Invalid idle_threshold_seconds value '{value}': not a number. "
            f"Using default: {IDLE_THRESHOLD_DEFAULT}s"
        )
        return IDLE_THRESHOLD_DEFAULT

    if value < IDLE_THRESHOLD_MIN:
        logging.warning(
            f"idle_threshold_seconds value {value}s is below minimum ({IDLE_THRESHOLD_MIN}s). "
            f"Using default: {IDLE_THRESHOLD_DEFAULT}s"
        )
        return IDLE_THRESHOLD_DEFAULT

    if value > IDLE_THRESHOLD_MAX:
        logging.warning(
            f"idle_threshold_seconds value {value}s exceeds maximum ({IDLE_THRESHOLD_MAX}s). "
            f"Using default: {IDLE_THRESHOLD_DEFAULT}s"
        )
        return IDLE_THRESHOLD_DEFAULT

    return value


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
        url_extraction_enabled: Enable browser URL extraction (default: True)
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
        transition_prompt_enabled: Enable transition detection prompts (default: True)
        transition_sensitivity: Prompt aggressiveness level (default: moderate)
        transition_never_prompt_apps: Apps where prompts are never shown (default: common editing apps)
        interaction_threshold_seconds: Seconds of recent typing/clicking to mark as active (default: 5.0)
        categorization_confidence_threshold: Minimum confidence score for automatic categorization (default: 70)
        archive_enabled: Enable automatic screenshot archiving (default: True)
        archive_check_interval_hours: Hours between archive checks (default: 24)
        llm_provider: LLM provider to use - 'openai' or 'anthropic' (default: openai)
        llm_api_key: API key or environment variable name (default: empty string)
        billing_increment: Minutes per billing increment (default: 6 = 0.1 hour)
        night_processing_enabled: Enable night processing mode (default: True)
        night_processing_start_hour: Hour when night mode begins (default: 18)
        night_processing_end_hour: Hour when night mode ends (default: 8)
        night_processing_idle_minutes: Idle minutes required to trigger night processing (default: 30)
        night_processing_batch_size: Number of activities to process per batch (default: 50)
    """
    poll_interval_seconds: float = 1.0
    idle_threshold_seconds: float = 180.0
    merge_threshold_seconds: float = 2.0
    database_path: Optional[str] = None
    start_on_boot: bool = False
    start_tracking_on_launch: bool = True
    url_extraction_enabled: bool = True
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
    # Transition detection & smart prompts
    transition_prompt_enabled: bool = True
    transition_sensitivity: str = "moderate"
    transition_never_prompt_apps: List[str] = field(default_factory=lambda: ["WINWORD.EXE", "EXCEL.EXE", "Teams.exe", "Zoom.exe"])
    # Interaction level detection
    interaction_threshold_seconds: float = 5.0
    # Activity-to-Matter categorization
    categorization_confidence_threshold: int = 70
    # Archive settings
    archive_enabled: bool = True
    archive_check_interval_hours: int = 24
    # LLM settings
    llm_provider: str = "openai"
    llm_api_key: str = ""
    billing_increment: int = 6
    # Resource monitoring settings
    resource_cpu_threshold: float = 80.0
    resource_memory_threshold_mb: int = 200
    resource_battery_threshold: int = 20
    resource_monitoring_interval_seconds: int = 60
    # Night processing settings
    night_processing_enabled: bool = True
    night_processing_start_hour: int = 18
    night_processing_end_hour: int = 8
    night_processing_idle_minutes: int = 30
    night_processing_batch_size: int = 50

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

        # Apply validation for idle_threshold_seconds
        if 'idle_threshold_seconds' in valid_fields:
            valid_fields['idle_threshold_seconds'] = validate_idle_threshold(
                valid_fields['idle_threshold_seconds']
            )

        return cls(**valid_fields)
