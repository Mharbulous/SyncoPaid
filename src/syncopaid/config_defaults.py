"""
Default configuration values for SyncoPaid.

Contains all default settings for polling intervals, thresholds,
screenshot settings, and action screenshot settings.
"""

# Default configuration values
DEFAULT_CONFIG = {
    "poll_interval_seconds": 1.0,
    "idle_threshold_seconds": 180,
    "merge_threshold_seconds": 2.0,
    "database_path": None,  # Will be set to default location if None
    "start_on_boot": False,
    "start_tracking_on_launch": True,
    "url_extraction_enabled": True,
    # Screenshot settings (periodic)
    "screenshot_enabled": True,
    "screenshot_interval_seconds": 10,
    "screenshot_threshold_identical": 0.92,
    "screenshot_threshold_significant": 0.70,
    "screenshot_threshold_identical_same_window": 0.90,
    "screenshot_threshold_identical_different_window": 0.99,
    "screenshot_quality": 65,
    "screenshot_max_dimension": 1920,
    # Action screenshot settings
    "action_screenshot_enabled": True,
    "action_screenshot_throttle_seconds": 0.5,
    "action_screenshot_quality": 65,
    "action_screenshot_max_dimension": 1920,
    # Idle resumption detection
    "minimum_idle_duration_seconds": 180,
    # UI automation settings
    "ui_automation_enabled": True,
    "ui_automation_outlook_enabled": True,
    "ui_automation_explorer_enabled": True,
    # Transition detection & smart prompts
    "transition_prompt_enabled": True,
    "transition_sensitivity": "moderate",  # aggressive, moderate, minimal
    "transition_never_prompt_apps": ["WINWORD.EXE", "EXCEL.EXE", "Teams.exe", "Zoom.exe"],
    # Interaction level detection
    "interaction_threshold_seconds": 5.0,
    # Activity-to-Matter categorization
    "categorization_confidence_threshold": 70,
    # Archive settings
    "archive_enabled": True,
    "archive_check_interval_hours": 24,
    # LLM settings
    "llm_provider": "openai",  # 'openai' or 'anthropic'
    "llm_api_key": "",         # API key (or env var name)
    "billing_increment": 6,    # Minutes per billing increment (default: 6 = 0.1 hour)
    # Resource monitoring settings
    "resource_cpu_threshold": 80.0,
    "resource_memory_threshold_mb": 200,
    "resource_battery_threshold": 20,
    "resource_monitoring_interval_seconds": 60,
    # Night processing settings
    "night_processing_enabled": True,
    "night_processing_start_hour": 18,  # 6 PM
    "night_processing_end_hour": 8,     # 8 AM
    "night_processing_idle_minutes": 30,
    "night_processing_batch_size": 50,
}
