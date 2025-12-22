# tests/test_import_dialog.py
import sys
import pytest
from unittest.mock import patch, Mock, MagicMock

# Mock all Windows-specific and GUI modules before importing
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
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

def test_show_import_dialog_exists():
    """Test that show_import_dialog function exists and is callable."""
    from syncopaid.main_ui_windows import show_import_dialog
    assert callable(show_import_dialog)

def test_show_import_dialog_starts_thread():
    """Test that dialog runs in a daemon thread."""
    with patch('syncopaid.main_ui_windows.threading.Thread') as mock_thread:
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        from syncopaid.main_ui_windows import show_import_dialog
        show_import_dialog(None)

        mock_thread.assert_called_once()
        assert mock_thread.call_args.kwargs.get('daemon') == True
        mock_thread_instance.start.assert_called_once()
