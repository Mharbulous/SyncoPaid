"""Extract contextual information from window titles."""
import re
import logging

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

def extract_subject_from_outlook(app: str, title: str) -> str:
    """
    Extract email subject from Outlook window title.

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted email subject, or None if no subject found
    """
    if not app or not title:
        return None

    # Check if this is Outlook
    if app.upper() != "OUTLOOK.EXE":
        return None

    # Format 1: "Inbox - SUBJECT - email@domain - Outlook"
    # Format 2: "SUBJECT - Message (HTML) - Outlook"

    # Remove trailing " - Outlook" first
    if title.endswith(" - Outlook"):
        title = title[:-10].strip()
    else:
        return None

    # Split by " - " separator
    parts = title.split(" - ")

    if len(parts) < 2:
        return None

    # Format 1: "Inbox - SUBJECT - email@domain"
    if parts[0] == "Inbox" and len(parts) >= 2:
        # Subject is second part, unless it's just an email
        subject = parts[1]
        # Skip if it's just an email address (no actual subject)
        if "@" in subject and len(parts) == 2:
            return None
        return subject

    # Format 2: "SUBJECT - Message (HTML)"
    if len(parts) >= 2 and "Message" in parts[-1]:
        return parts[0]

    return None

# Office application executable names
OFFICE_APPS = {
    'WINWORD.EXE': 'Word',
    'EXCEL.EXE': 'Excel',
    'POWERPNT.EXE': 'PowerPoint',
    'MSPUB.EXE': 'Publisher',
    'MSACCESS.EXE': 'Access'
}

def extract_filepath_from_office(app: str, title: str) -> str:
    """
    Extract file path from Office application window title.

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted file path/name, or None if not found
    """
    if not app or not title:
        return None

    # Check if this is an Office app
    app_upper = app.upper()
    if app_upper not in OFFICE_APPS:
        return None

    app_name = OFFICE_APPS[app_upper]

    # Format: "FILEPATH - AppName"
    separator = f" - {app_name}"
    if separator not in title:
        return None

    # Extract everything before the separator
    filepath = title.split(separator)[0].strip()

    if filepath:
        return filepath

    return None
