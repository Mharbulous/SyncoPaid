"""Extract contextual information from window titles."""
import re
import logging

# Browser executable names (case-insensitive matching)
BROWSER_APPS = {'chrome.exe', 'msedge.exe', 'firefox.exe', 'brave.exe', 'opera.exe'}

# Legal research platforms (desktop apps and browser patterns)
LEGAL_RESEARCH_APPS = {
    'westlaw.exe', 'westlawnext.exe', 'lexisnexis.exe',
    'fastcase.exe', 'casetext.exe'
}

LEGAL_RESEARCH_BROWSER_PATTERNS = [
    'westlaw', 'canlii', 'lexisnexis', 'lexis+',
    'fastcase', 'casetext', 'courtlistener', 'justia'
]

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

def extract_context(app: str, title: str) -> str:
    """
    Extract contextual information from window title based on application type.

    Routes to appropriate extraction function:
    - Browsers → URL extraction
    - Outlook → Email subject extraction
    - Office apps → File path extraction

    Args:
        app: Application executable name (e.g., 'chrome.exe', 'OUTLOOK.EXE')
        title: Window title text

    Returns:
        Extracted context string (URL, subject, or filepath), or None if nothing extracted
    """
    if not app or not title:
        return None

    try:
        # Try browser URL extraction
        url = extract_url_from_browser(app, title)
        if url:
            return url

        # Try Outlook subject extraction
        subject = extract_subject_from_outlook(app, title)
        if subject:
            return subject

        # Try Office filepath extraction
        filepath = extract_filepath_from_office(app, title)
        if filepath:
            return filepath

        return None

    except Exception as e:
        # Log but don't crash - graceful degradation
        logging.debug(f"Context extraction failed for {app}: {e}")
        return None

def is_legal_research_app(app: str, title: str = None) -> bool:
    """
    Detect if window is a legal research application.

    Args:
        app: Application executable name
        title: Window title (optional, for browser detection)

    Returns:
        True if legal research app/site, False otherwise
    """
    if not app:
        return False

    # Check desktop apps
    if app.lower() in LEGAL_RESEARCH_APPS:
        return True

    # Check browser tabs for legal research sites
    if app.lower() in BROWSER_APPS and title:
        title_lower = title.lower()
        return any(pattern in title_lower for pattern in LEGAL_RESEARCH_BROWSER_PATTERNS)

    return False
