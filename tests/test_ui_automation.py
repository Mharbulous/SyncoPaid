import pytest


def test_pywinauto_available():
    """Test that pywinauto library is installed and importable."""
    try:
        import pywinauto
        assert pywinauto is not None
    except ImportError:
        pytest.fail("pywinauto library not installed")


def test_outlook_extractor_interface():
    from syncopaid.ui_automation import OutlookExtractor
    extractor = OutlookExtractor()
    result = extractor.extract({'app': 'OUTLOOK.EXE', 'title': 'Inbox', 'pid': 1234})
    assert result is None or isinstance(result, dict)
    assert extractor.timeout_ms == 100


def test_explorer_extractor_interface():
    from syncopaid.ui_automation import ExplorerExtractor
    extractor = ExplorerExtractor()
    result = extractor.extract({'app': 'explorer.exe', 'title': 'Cases', 'pid': 5678})
    assert result is None or isinstance(result, dict)
    assert extractor.timeout_ms == 100


def test_outlook_extractor_returns_subject_and_sender():
    from syncopaid.ui_automation import OutlookExtractor, PYWINAUTO_AVAILABLE
    from unittest.mock import MagicMock, patch
    import sys

    extractor = OutlookExtractor()

    # Skip test on non-Windows platforms
    if not PYWINAUTO_AVAILABLE:
        pytest.skip("pywinauto not available on this platform")

    with patch('syncopaid.ui_automation.Application') as mock_app:
        mock_window = MagicMock()
        mock_subject = MagicMock()
        mock_subject.window_text.return_value = "Re: Smith Case"
        mock_sender = MagicMock()
        mock_sender.window_text.return_value = "client@example.com"

        mock_window.child_window.side_effect = [mock_subject, mock_sender]
        mock_app.return_value.connect.return_value.window.return_value = mock_window

        result = extractor.extract({
            'app': 'OUTLOOK.EXE',
            'title': 'Re: Smith Case - Outlook',
            'pid': 1234
        })

        assert result is not None
        assert result['email_subject'] == "Re: Smith Case"
        assert result['sender'] == "client@example.com"
