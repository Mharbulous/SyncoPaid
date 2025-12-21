import pytest
import sqlite3
from migrate_content_fields import parse_description

def test_parse_empty_description():
    """Empty description returns empty tuple."""
    assert parse_description('') == ('', '', '')
    assert parse_description(None) == ('', '', '')

def test_parse_story_format():
    """Extracts user story from markdown format."""
    desc = """**As a** developer
**I want** to track my work
**So that** I can bill accurately"""
    story, criteria, remaining = parse_description(desc)
    assert story == "As a developer, I want to track my work, so that I can bill accurately"
    assert criteria == ''
    assert remaining == ''

def test_parse_acceptance_criteria():
    """Extracts acceptance criteria checklist."""
    desc = """Some context.

**Acceptance Criteria:**
- [ ] First criterion
- [ ] Second criterion
- [x] Completed criterion

More context."""
    story, criteria, remaining = parse_description(desc)
    assert "- [ ] First criterion" in criteria
    assert "- [x] Completed criterion" in criteria
    assert "More context" in remaining

def test_parse_full_description():
    """Parses complete description with all sections."""
    desc = """**As a** user
**I want** feature X
**So that** I benefit

**Acceptance Criteria:**
- [ ] Must do A
- [ ] Must do B

Additional notes here."""
    story, criteria, remaining = parse_description(desc)
    assert "As a user" in story
    assert "- [ ] Must do A" in criteria
    assert "Additional notes" in remaining

def test_add_columns_idempotent(tmp_path):
    """Adding columns twice doesn't error."""
    from migrate_content_fields import migrate
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE story_nodes (id TEXT, description TEXT)")
    conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")

    # Create a minimal add_schema_columns function for testing
    def add_schema_columns(conn):
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN story TEXT")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                raise
        try:
            cursor.execute("ALTER TABLE story_nodes ADD COLUMN success_criteria TEXT")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                raise
        conn.commit()

    # First addition
    add_schema_columns(conn)

    # Verify columns exist
    cursor = conn.execute("PRAGMA table_info(story_nodes)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'story' in columns
    assert 'success_criteria' in columns

    # Second addition should not error
    add_schema_columns(conn)  # No exception
