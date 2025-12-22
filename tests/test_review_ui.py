"""Tests for review UI."""
import pytest
import sys
from unittest.mock import Mock, MagicMock

# Mock tkinter for headless environments
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

from syncopaid.review_ui import ReviewUI, ReviewEntry


def test_review_entry_creation():
    entry = ReviewEntry(
        event_id=1,
        matter='Matter 123',
        narrative='Research',
        time_hours=0.2
    )
    assert entry.event_id == 1
    assert entry.matter == 'Matter 123'
    assert entry.status is None


def test_review_ui_initialization():
    ui = ReviewUI()
    assert ui.current_entry is None
    assert ui.status is None


def test_review_entry_approval():
    ui = ReviewUI()
    entry = ReviewEntry(1, 'Matter 123', 'Research', 0.2)
    ui.load_entry(entry)
    ui.approve()
    assert ui.get_status() == 'approved'


def test_review_load_entries():
    ui = ReviewUI()
    entries = [
        ReviewEntry(1, 'M1', 'Work 1', 0.1),
        ReviewEntry(2, 'M2', 'Work 2', 0.2),
    ]
    ui.load_entries(entries)
    assert len(ui.entries) == 2
