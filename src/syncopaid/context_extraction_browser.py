"""Browser URL extraction from window titles."""
import re

# Browser executable names (case-insensitive matching)
BROWSER_APPS = {'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe'}

def extract_url_from_browser(app: str, title: str) -> str:
    """
    Extract URL from browser window title.

    Args:
        app: Application executable name (e.g., 'chrome.exe')
        title: Window title text

    Returns:
        Extracted URL string, or None if no URL found
    """
    if not app or not title:
        return None

    # Check if this is a browser
    if app.lower() not in BROWSER_APPS:
        return None

    # Pattern matches http:// or https:// URLs
    # Looks for protocol + domain + optional path
    url_pattern = r'https?://[^\s<>"\'\[\]{}|\\^`]+'

    match = re.search(url_pattern, title)
    if match:
        return match.group(0)

    return None
