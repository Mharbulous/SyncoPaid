# 027: UI Automation - Foundation (Dependencies & DB Schema)

## Task
Add pywinauto dependency and extend events table with metadata column.

## Context
This is the first step for UI automation integration (from original story 8.3). Sets up the foundation for extracting rich context from Outlook and Explorer.

## Scope
- Add pywinauto>=0.6.8 to requirements.txt
- Add `metadata` TEXT column to events table (stores JSON)
- Update insert_event() and get_events() to handle metadata

## Key Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Add pywinauto dependency |
| `src/syncopaid/database.py` | Schema migration for metadata column |
| `src/syncopaid/tracker.py` | Add metadata field to ActivityEvent |
| `tests/test_ui_automation.py` | Test pywinauto availability |
| `tests/test_database.py` | Test metadata storage |

## Implementation Steps

### Step 1: Add pywinauto test

```python
# tests/test_ui_automation.py (CREATE)
import pytest

def test_pywinauto_available():
    """Test that pywinauto library is installed and importable."""
    try:
        import pywinauto
        assert pywinauto is not None
    except ImportError:
        pytest.fail("pywinauto library not installed")
```

### Step 2: Add pywinauto to requirements

```
# requirements.txt (add line)
pywinauto>=0.6.8
```

Run: `pip install pywinauto`

### Step 3: Extend ActivityEvent with metadata field

```python
# src/syncopaid/tracker.py - modify ActivityEvent dataclass
metadata: Optional[Dict[str, str]] = None  # Add this field
```

### Step 4: Add metadata column migration

```python
# src/syncopaid/database.py - in _migrate_events_table()
if 'metadata' not in columns:
    cursor.execute("ALTER TABLE events ADD COLUMN metadata TEXT")
    logging.info("Database migration: Added metadata column to events table")
```

### Step 5: Update insert_event() for metadata

```python
# Serialize metadata to JSON if present
import json
metadata_json = json.dumps(metadata) if metadata else None
# Include in INSERT statement
```

### Step 6: Update get_events() to deserialize metadata

```python
# Deserialize metadata JSON if present
if 'metadata' in row.keys() and row['metadata']:
    metadata = json.loads(row['metadata'])
```

## Verification

```bash
venv\Scripts\activate
pip install pywinauto
python -m pytest tests/test_ui_automation.py::test_pywinauto_available -v
python -m pytest tests/test_database.py -v
python -m syncopaid.database  # Verify migration runs
```

## Dependencies
None - this is the first sub-plan.

## Next Task
After this: `028_ui-automation-module.md`
