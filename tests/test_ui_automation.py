import pytest


def test_pywinauto_available():
    """Test that pywinauto library is installed and importable."""
    try:
        import pywinauto
        assert pywinauto is not None
    except ImportError:
        pytest.fail("pywinauto library not installed")
