import pytest
from datetime import datetime, timedelta


def test_timeline_block_creation():
    """Test creating a timeline block from event data."""
    from syncopaid.timeline_view import TimelineBlock

    block = TimelineBlock(
        start_time=datetime(2025, 12, 21, 9, 0, 0),
        end_time=datetime(2025, 12, 21, 9, 30, 0),
        app="WINWORD.EXE",
        title="Contract Draft - Word",
        is_idle=False
    )

    assert block.duration_seconds == 1800  # 30 minutes
    assert block.app == "WINWORD.EXE"
    assert block.is_idle == False


def test_timeline_block_from_event():
    """Test creating timeline block from database event dict."""
    from syncopaid.timeline_view import TimelineBlock

    event = {
        'timestamp': '2025-12-21T09:00:00',
        'end_time': '2025-12-21T09:30:00',
        'duration_seconds': 1800,
        'app': 'chrome.exe',
        'title': 'Legal Research - Chrome',
        'is_idle': False
    }

    block = TimelineBlock.from_event(event)

    assert block.app == 'chrome.exe'
    assert block.duration_seconds == 1800


def test_timeline_block_color_by_app():
    """Test that blocks get consistent colors by application."""
    from syncopaid.timeline_view import TimelineBlock, get_app_color

    # Same app should get same color
    color1 = get_app_color("WINWORD.EXE")
    color2 = get_app_color("WINWORD.EXE")
    assert color1 == color2

    # Idle should be distinct (gray)
    idle_color = get_app_color(None, is_idle=True)
    assert idle_color == "#D3D3D3"  # Light gray
