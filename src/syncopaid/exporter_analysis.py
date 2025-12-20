"""
Statistical analysis functions for export operations.

Provides functions for calculating aggregate statistics and breakdowns
from activity event data.
"""

from typing import List, Dict


def calculate_app_breakdown(events: List[Dict]) -> List[Dict]:
    """
    Calculate time spent per application.

    Args:
        events: List of event dictionaries

    Returns:
        List of {app, duration_seconds, duration_hours, percentage} dictionaries,
        sorted by duration (descending)
    """
    # Aggregate by app
    app_totals = {}
    total_duration = 0

    for event in events:
        if event['is_idle']:
            continue

        # Skip events without duration
        if event['duration_seconds'] is None:
            continue

        app = event['app'] or 'unknown'
        duration = event['duration_seconds']

        app_totals[app] = app_totals.get(app, 0) + duration
        total_duration += duration

    # Convert to list and calculate percentages
    breakdown = []
    for app, duration in sorted(app_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (duration / total_duration * 100) if total_duration > 0 else 0
        breakdown.append({
            "app": app,
            "duration_seconds": round(duration, 2),
            "duration_hours": round(duration / 3600, 2),
            "percentage": round(percentage, 1)
        })

    return breakdown


def calculate_duration_stats(events: List[Dict]) -> Dict[str, float]:
    """
    Calculate duration statistics from events.

    Args:
        events: List of event dictionaries

    Returns:
        Dictionary with total_duration, active_duration, and idle_duration
        (all in seconds)
    """
    total_duration = sum(
        e['duration_seconds'] for e in events
        if e['duration_seconds'] is not None
    )
    active_duration = sum(
        e['duration_seconds'] for e in events
        if not e['is_idle'] and e['duration_seconds'] is not None
    )
    idle_duration = sum(
        e['duration_seconds'] for e in events
        if e['is_idle'] and e['duration_seconds'] is not None
    )

    return {
        'total_duration': total_duration,
        'active_duration': active_duration,
        'idle_duration': idle_duration
    }
