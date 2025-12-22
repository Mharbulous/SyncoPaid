"""Billing utilities for time rounding and narrative generation."""
import math
import logging
from typing import List, Dict, Optional
from .llm import LLMClient


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


def generate_billing_narrative(
    activities: List[Dict],
    llm_client: Optional[LLMClient] = None
) -> str:
    """
    Generate a billing narrative from multiple activities.

    Combines related activities into a professional billing description
    suitable for client invoices.

    Args:
        activities: List of activity dicts with 'app' and 'title' keys
        llm_client: Optional LLM client for AI-powered generation

    Returns:
        Professional billing narrative string

    Example:
        activities = [
            {'app': 'Chrome', 'title': 'Estate Tax Research'},
            {'app': 'Word', 'title': 'Trust Amendment Draft.docx'}
        ]
        -> "Researched estate tax implications; drafted trust amendment"
    """
    if not activities:
        return ""

    # Combine activity descriptions
    combined = "; ".join([
        f"{a.get('app', 'Unknown')}: {a.get('title', 'No title')}"
        for a in activities
    ])

    if llm_client:
        # Use LLM to generate professional narrative
        try:
            result = llm_client.generate_narrative(combined)
            return result
        except Exception as e:
            logging.warning(f"LLM narrative generation failed: {e}")
            # Fall through to basic generation

    # Basic narrative without LLM
    return _generate_basic_narrative(activities)


def _generate_basic_narrative(activities: List[Dict]) -> str:
    """
    Generate a basic narrative without LLM.

    Extracts key terms from activities and formats them professionally.
    """
    terms = set()

    for activity in activities:
        title = activity.get('title', '')
        app = activity.get('app', '').lower()

        # Extract meaningful terms from title
        if title:
            # Remove file extensions and common suffixes
            clean_title = title.split(' - ')[0]  # Remove app name suffix
            clean_title = clean_title.replace('.docx', '').replace('.pdf', '')
            if clean_title:
                terms.add(clean_title)

        # Add app-specific context
        if 'word' in app or 'winword' in app:
            terms.add('document drafting')
        elif 'outlook' in app:
            terms.add('correspondence')
        elif 'chrome' in app or 'edge' in app or 'firefox' in app:
            terms.add('research')
        elif 'excel' in app:
            terms.add('data analysis')

    if terms:
        return "; ".join(sorted(terms)[:5])  # Limit to 5 terms

    return "General work activities"
