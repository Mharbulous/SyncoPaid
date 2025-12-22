import pytest
from datetime import datetime, timedelta
import tempfile
from pathlib import Path


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


def test_get_timeline_blocks_for_date():
    """Test fetching timeline blocks for a specific date."""
    from syncopaid.timeline_view import get_timeline_blocks
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Insert test events
        events = [
            ActivityEvent(
                timestamp="2025-12-21T09:00:00",
                duration_seconds=1800,
                app="WINWORD.EXE",
                title="Contract.docx",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-21T09:30:00",
                duration_seconds=600,
                app=None,
                title=None,
                is_idle=True
            ),
            ActivityEvent(
                timestamp="2025-12-21T09:40:00",
                duration_seconds=1200,
                app="chrome.exe",
                title="CanLII Research",
                is_idle=False
            ),
        ]
        db.insert_events_batch(events)

        # Get blocks for the date
        blocks = get_timeline_blocks(db, "2025-12-21")

        assert len(blocks) == 3
        assert blocks[0].app == "WINWORD.EXE"
        assert blocks[1].is_idle == True
        assert blocks[2].app == "chrome.exe"


def test_get_timeline_blocks_filter_by_app():
    """Test filtering timeline blocks by application."""
    from syncopaid.timeline_view import get_timeline_blocks
    from syncopaid.database import Database
    from syncopaid.tracker import ActivityEvent

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        events = [
            ActivityEvent(
                timestamp="2025-12-21T09:00:00",
                duration_seconds=1800,
                app="WINWORD.EXE",
                title="Doc1",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-21T09:30:00",
                duration_seconds=1200,
                app="chrome.exe",
                title="Web",
                is_idle=False
            ),
        ]
        db.insert_events_batch(events)

        # Filter by Word only
        blocks = get_timeline_blocks(db, "2025-12-21", app_filter="WINWORD.EXE")

        assert len(blocks) == 1
        assert blocks[0].app == "WINWORD.EXE"
