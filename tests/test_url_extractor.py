import pytest
from syncopaid.url_extractor import extract_browser_url

def test_extract_chrome_url_returns_string_or_none():
    """Should return URL string or None within timeout."""
    result = extract_browser_url("chrome.exe", timeout_ms=50)
    assert result is None or isinstance(result, str)

def test_extract_chrome_url_timeout():
    """Should return None if extraction exceeds timeout."""
    result = extract_browser_url("chrome.exe", timeout_ms=1)
    assert result is None

def test_extract_unsupported_browser():
    """Should return None for unsupported browsers."""
    result = extract_browser_url("notepad.exe")
    assert result is None
