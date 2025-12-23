"""Office application file path extraction from window titles."""

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
