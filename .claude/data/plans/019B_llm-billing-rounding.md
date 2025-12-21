# 019B: LLM & AI Integration - Billing Increment Rounding
Story ID: 8.5

## Task
Implement 6-minute billing increment rounding logic.

## Context
Law firms typically bill in 6-minute (0.1 hour) increments. This module provides functions to round activity durations to the appropriate billing increments.

## Scope
- Create `src/syncopaid/billing.py` module
- round_to_increment() function
- Support for configurable increment (default 6 minutes)

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/billing.py` | New module (CREATE) |
| `tests/test_billing.py` | Create test file |

## Implementation

```python
# src/syncopaid/billing.py (CREATE)
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
```

### Tests

```python
# tests/test_billing.py (CREATE)
"""Tests for billing utilities."""
import pytest
from syncopaid.billing import round_to_increment, minutes_to_hours, format_billing_time


def test_round_to_billing_increment():
    assert round_to_increment(5, 6) == 6     # 5 min -> 6 min
    assert round_to_increment(7, 6) == 12    # 7 min -> 12 min
    assert round_to_increment(120, 6) == 120  # 2 hours exact
    assert round_to_increment(1, 6) == 6     # minimum billing
    assert round_to_increment(0, 6) == 0     # zero stays zero


def test_round_to_increment_edge_cases():
    assert round_to_increment(6, 6) == 6     # exactly 6 min
    assert round_to_increment(12, 6) == 12   # exactly 12 min
    assert round_to_increment(6.5, 6) == 12  # fractional rounds up


def test_minutes_to_hours():
    assert minutes_to_hours(6) == 0.1
    assert minutes_to_hours(12) == 0.2
    assert minutes_to_hours(60) == 1.0
    assert minutes_to_hours(90) == 1.5


def test_format_billing_time():
    assert format_billing_time(6) == "0.1 hours"
    assert format_billing_time(60) == "1.0 hour"
    assert format_billing_time(90) == "1.5 hours"


if __name__ == "__main__":
    test_round_to_billing_increment()
    test_round_to_increment_edge_cases()
    test_minutes_to_hours()
    test_format_billing_time()
    print("All tests passed!")
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_billing.py -v
python -c "from syncopaid.billing import round_to_increment; print(round_to_increment(7))"
```

## Dependencies
- Task 019A (LLM API client)

## Next Task
After this: `019C_llm-narrative-generation.md`
