# 022C1: Import Clients & Matters - Database Save Function
Story ID: 8.1.2

## Task
Implement the `save_import_to_database()` function for persisting imported client/matter data.

## Context
This function takes an ImportResult from the folder parser (022B) and saves clients/matters to the database. It's decoupled from the UI for testability.

## Scope
- Add `save_import_to_database()` to `main_ui_windows.py`
- Insert clients first, capture IDs
- Insert matters with client_id foreign key
- Use INSERT OR IGNORE for idempotency

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_ui_windows.py` | Add save function here |
| `src/syncopaid/client_matter_importer.py` | ImportResult dataclass (from 022B) |
| `src/syncopaid/database.py` | Database connection |

## TDD Tasks

### Task 1: Implement save_import_to_database function

**Test First**:
```python
# tests/test_import_database.py
import pytest
from unittest.mock import Mock, MagicMock, patch
from syncopaid.client_matter_importer import ImportResult, ClientInfo, MatterInfo

def test_save_import_to_database_inserts_clients():
    """Test that clients are inserted into database."""
    from syncopaid.main_ui_windows import save_import_to_database

    # Create mock import result
    client = ClientInfo(
        display_name="Smith, John",
        folder_path="/path/to/Smith, John"
    )
    matter = MatterInfo(
        display_name="Real Estate Purchase",
        folder_path="/path/to/Smith, John/Real Estate Purchase",
        client_display_name="Smith, John"
    )
    import_result = ImportResult(
        clients=[client],
        matters=[matter],
        stats={'clients': 1, 'matters': 1}
    )

    # Mock database
    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)  # Return client ID
    mock_db._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
    mock_db._get_connection.return_value.__exit__ = Mock(return_value=False)

    # Execute
    save_import_to_database(mock_db, import_result)

    # Verify client insert was called
    calls = mock_cursor.execute.call_args_list
    assert any("INSERT" in str(call) and "clients" in str(call) for call in calls)
```

**Implementation**:
```python
def save_import_to_database(database, import_result):
    """Save imported clients and matters to database."""
    with database._get_connection() as conn:
        cursor = conn.cursor()

        # Build client ID map
        client_ids = {}
        for client in import_result.clients:
            cursor.execute("""
                INSERT OR IGNORE INTO clients (display_name, folder_path)
                VALUES (?, ?)
            """, (client.display_name, client.folder_path))

            cursor.execute(
                "SELECT id FROM clients WHERE display_name = ?",
                (client.display_name,)
            )
            row = cursor.fetchone()
            if row:
                client_ids[client.display_name] = row[0]

        # Insert matters
        for matter in import_result.matters:
            client_id = client_ids.get(matter.client_display_name)
            if client_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO matters
                    (client_id, display_name, folder_path)
                    VALUES (?, ?, ?)
                """, (client_id, matter.display_name, matter.folder_path))

        conn.commit()
```

### Task 2: Test matters insertion with foreign key

**Test**:
```python
def test_save_import_to_database_inserts_matters_with_client_id():
    """Test that matters are inserted with correct client_id foreign key."""
    from syncopaid.main_ui_windows import save_import_to_database

    client = ClientInfo(
        display_name="Johnson Corp",
        folder_path="/path/to/Johnson Corp"
    )
    matter = MatterInfo(
        display_name="Contract Dispute",
        folder_path="/path/to/Johnson Corp/Contract Dispute",
        client_display_name="Johnson Corp"
    )
    import_result = ImportResult(
        clients=[client],
        matters=[matter],
        stats={'clients': 1, 'matters': 1}
    )

    mock_db = Mock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (42,)  # Client ID = 42
    mock_db._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
    mock_db._get_connection.return_value.__exit__ = Mock(return_value=False)

    save_import_to_database(mock_db, import_result)

    # Verify matters insert was called with client_id
    calls = mock_cursor.execute.call_args_list
    assert any("INSERT" in str(call) and "matters" in str(call) for call in calls)
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_import_database.py -v
```

## Dependencies
- Task 022A (database schema with clients/matters tables)
- Task 022B (ImportResult, ClientInfo, MatterInfo dataclasses)

## Next Task
After this: `022C2_import-clients-matters-dialog-ui.md`
