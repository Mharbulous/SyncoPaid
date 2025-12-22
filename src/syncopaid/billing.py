"""Billing utilities for time rounding and narrative generation."""
import math
from typing import List, Dict


def round_to_increment(minutes: float, increment: int = 6) -> int:
    """
    Round minutes to billing increment.

    Standard legal billing uses 6-minute increments (0.1 hour).
    Always rounds UP to ensure minimum billing.

    Args:
        minutes: Duration in minutes
        increment: Billing increment in minutes (default 6)

    Returns:
        Rounded duration in minutes

    Examples:
        round_to_increment(5, 6) -> 6    # 5 min -> 0.1 hour
        round_to_increment(7, 6) -> 12   # 7 min -> 0.2 hour
        round_to_increment(120, 6) -> 120  # 2 hours exact
    """
    if minutes <= 0:
        return 0
    return math.ceil(minutes / increment) * increment


def minutes_to_hours(minutes: int) -> float:
    """
    Convert billing minutes to decimal hours.

    Args:
        minutes: Duration in minutes (should be multiple of 6)

    Returns:
        Decimal hours (e.g., 6 minutes = 0.1 hours)
    """
    return round(minutes / 60, 1)


def format_billing_time(minutes: int) -> str:
    """
    Format billing time for display.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string like "0.5 hours" or "1.0 hour"
    """
    hours = minutes_to_hours(minutes)
    unit = "hour" if hours == 1.0 else "hours"
    return f"{hours} {unit}"
