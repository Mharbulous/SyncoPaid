"""
Tests for migrate_content_fields.py
"""
import sys
from pathlib import Path

# Add parent directory to path to import the migration module
sys.path.insert(0, str(Path(__file__).parent.parent))

from migrate_content_fields import parse_description


def test_parse_description_with_full_content():
    desc = """**As a** developer **I want** feature X **So that** benefit Y

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

Additional context here."""
    story, criteria, remaining = parse_description(desc)
    assert "As a developer" in story
    assert "Criterion 1" in criteria
    assert "Additional context" in remaining


def test_parse_description_empty():
    assert parse_description('') == ('', '', '')


def test_parse_description_no_structured_content():
    desc = "Just plain text without structure"
    story, criteria, remaining = parse_description(desc)
    assert story == ''
    assert criteria == ''
    assert remaining == desc
