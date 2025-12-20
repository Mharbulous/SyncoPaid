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
