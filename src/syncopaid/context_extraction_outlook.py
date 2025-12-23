"""Outlook email subject extraction from window titles."""

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
