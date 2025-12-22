# tests/test_import_database.py
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch

# Mock all Windows-specific and GUI modules before importing
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['pynput'] = MagicMock()
sys.modules['pynput.keyboard'] = MagicMock()
sys.modules['pynput.mouse'] = MagicMock()
sys.modules['syncopaid.tracker_windows_idle'] = MagicMock()
sys.modules['syncopaid.tracker_windows'] = MagicMock()

from syncopaid.client_matter_importer import ImportResult, ImportedClient, ImportedMatter

def test_save_import_to_database_inserts_clients():
    """Test that clients are inserted into database."""
    from syncopaid.main_ui_windows import save_import_to_database

    # Create mock import result
    client = ImportedClient(
        display_name="Smith, John",
        folder_path="/path/to/Smith, John"
    )
    matter = ImportedMatter(
        display_name="Real Estate Purchase",
        folder_path="/path/to/Smith, John/Real Estate Purchase",
        client_display_name="Smith, John"
    )
    import_result = ImportResult(
        clients=[client],
        matters=[matter],
        root_path="/path/to",
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
