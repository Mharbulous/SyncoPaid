"""
Event formatting functions for export operations.

Handles transformation of database events into various export formats,
including simplified LLM-ready JSON.
"""

import json
from typing import List, Dict, Optional


def format_events_for_export(events: List[Dict]) -> List[Dict]:
    """
    Format events for JSON export.

    Removes internal database IDs and ensures consistent format.

    Args:
        events: List of event dictionaries from database

    Returns:
        List of formatted event dictionaries
    """
    formatted = []

    for event in events:
        # Derive state from is_idle if not present (backward compatibility)
        state = event.get('state')
        if not state:
            state = 'Inactive' if event['is_idle'] else 'Active'

        formatted.append({
            "timestamp": event['timestamp'],
            "duration_seconds": event['duration_seconds'],
            "end_time": event.get('end_time'),
            "app": event['app'],
            "title": event['title'],
            "url": event['url'],
            "is_idle": event['is_idle'],
            "state": state
        })

    return formatted


def generate_llm_prompt_data(events: List[Dict]) -> str:
    """
    Generate a JSON string optimized for LLM prompts.

    This produces a simplified, compact format ideal for including
    in Claude/GPT prompts for automatic categorization.

    Args:
        events: List of event dictionaries (typically non-idle only)

    Returns:
        JSON string ready for LLM prompt
    """
    llm_events = []

    for event in events:
        # Extract time only (not full timestamp)
        time_str = event['timestamp'].split('T')[1][:8]  # HH:MM:SS

        # Handle None duration
        duration_min = None
        if event['duration_seconds'] is not None:
            duration_min = round(event['duration_seconds'] / 60, 1)

        # Derive state from is_idle if not present (backward compatibility)
        state = event.get('state')
        if not state:
            state = 'Active'  # Non-idle events default to Active

        llm_events.append({
            "time": time_str,
            "duration_min": duration_min,
            "app": event['app'],
            "title": event['title'],
            "state": state
        })

    return json.dumps(llm_events, indent=2)


def format_file_size(bytes: int) -> str:
    """
    Format file size in human-readable form.

    Args:
        bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"
