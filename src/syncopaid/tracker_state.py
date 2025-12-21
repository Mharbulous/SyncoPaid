"""
State constants, validation, and data models for activity tracking.

This module defines:
- State constants (Active, Inactive, etc.)
- Client matter pattern validation
- ActivityEvent and IdleResumptionEvent dataclasses
"""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


# ============================================================================
# STATE CONSTANTS AND VALIDATION
# ============================================================================

# System states (assigned automatically based on tracking conditions)
STATE_ACTIVE = "Active"       # Tracked activity, client matter TBD (default)
STATE_INACTIVE = "Inactive"   # Idle detected (keyboard/mouse inactivity)
STATE_OFF = "Off"             # SyncoPaid wasn't running (gaps)
STATE_BLOCKED = "Blocked"     # Auto-blocked content (passwords, incognito)
STATE_PAUSED = "Paused"       # User manually paused tracking

# User-assigned states (non-billable)
STATE_PERSONAL = "Personal"   # Personal time
STATE_ON_BREAK = "On-break"   # Break time

# States that can be converted to client matters
CONVERTIBLE_STATES = {STATE_ACTIVE, STATE_INACTIVE, STATE_OFF}

# All valid system/user states
VALID_STATES = {
    STATE_ACTIVE, STATE_INACTIVE, STATE_OFF, STATE_BLOCKED,
    STATE_PAUSED, STATE_PERSONAL, STATE_ON_BREAK
}

# Client matter pattern: 4 digits, dot, optional letter, 3 digits
# Examples: 1023.L213, 1214.001
CLIENT_MATTER_PATTERN = re.compile(r'^\d{4}\.[A-Z]?\d{3}$')


def is_valid_state(state: str) -> bool:
    """Check if state is valid (system state or client matter number)."""
    if state in VALID_STATES:
        return True
    return bool(CLIENT_MATTER_PATTERN.match(state))


def is_client_matter(state: str) -> bool:
    """Check if state is a client matter number (not a system state)."""
    return bool(CLIENT_MATTER_PATTERN.match(state))


def can_convert_to_matter(state: str) -> bool:
    """Check if a state can be converted to a client matter number."""
    return state in CONVERTIBLE_STATES


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ActivityEvent:
    """
    Represents a single captured activity event.

    This is the core data structure that will be stored in the database
    and exported for LLM processing.

    Fields:
        timestamp: Start time in ISO8601 format (e.g., "2025-12-09T10:30:45")
        duration_seconds: Duration in seconds (may be None for legacy records)
        end_time: End time in ISO8601 format (may be None for legacy records)
        app: Application executable name
        title: Window title
        url: URL if applicable (future enhancement)
        cmdline: Process command line arguments (list of strings)
        is_idle: Whether this was an idle period (deprecated - use state)
        state: Activity state or client matter number (e.g., "Active", "1023.L213")
        metadata: Optional JSON-serializable dict for UI automation context
    """
    timestamp: str  # ISO8601 format: "2025-12-09T10:30:45" (start time)
    duration_seconds: Optional[float]
    app: Optional[str]
    title: Optional[str]
    end_time: Optional[str] = None  # ISO8601 format (end time)
    url: Optional[str] = None
    cmdline: Optional[List[str]] = None  # Process command line arguments
    is_idle: bool = False
    state: str = STATE_ACTIVE  # Default to Active (client matter TBD)
    metadata: Optional[Dict[str, str]] = None  # UI automation context (JSON)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export or database storage."""
        return asdict(self)


@dataclass
class IdleResumptionEvent:
    """
    Event emitted when user resumes work after significant idle period.

    This event signals a natural transition point for prompting time categorization.
    Only emitted when idle period exceeds minimum_idle_duration threshold (default 180s).

    Fields:
        resumption_timestamp: ISO8601 timestamp when user became active again
        idle_duration: Duration of idle period in seconds
    """
    resumption_timestamp: str  # ISO8601 format: "2025-12-18T10:30:00+00:00"
    idle_duration: float  # Seconds user was idle

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export or event handling."""
        return asdict(self)
