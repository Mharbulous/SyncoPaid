"""
Core tracking module for capturing window activity and idle detection.

This module provides the TrackerLoop class which continuously monitors:
- Active window title and application
- User idle time (keyboard/mouse inactivity)
- Event merging to combine consecutive identical activities

All data is captured locally at second-level precision.
"""

import logging

# Re-export state types and constants for backwards compatibility
from syncopaid.tracker_state import (
    STATE_ACTIVE,
    STATE_INACTIVE,
    STATE_OFF,
    STATE_BLOCKED,
    STATE_PAUSED,
    STATE_PERSONAL,
    STATE_ON_BREAK,
    CONVERTIBLE_STATES,
    VALID_STATES,
    CLIENT_MATTER_PATTERN,
    is_valid_state,
    is_client_matter,
    can_convert_to_matter,
    InteractionLevel,
    ActivityEvent,
    IdleResumptionEvent
)

# Re-export Windows APIs availability flag and lock/screensaver detection
from syncopaid.tracker_windows import (
    WINDOWS_APIS_AVAILABLE,
    is_screensaver_active,
    is_workstation_locked,
    is_key_pressed,
    get_keyboard_activity,
    get_mouse_activity
)

# Import core TrackerLoop class
from syncopaid.tracker_loop import TrackerLoop

# Import testing utilities
from syncopaid.tracker_testing import run_console_test


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run console test
    run_console_test(TrackerLoop, duration_seconds=30)
