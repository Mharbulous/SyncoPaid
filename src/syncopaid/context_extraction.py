"""Extract contextual information from window titles."""
import logging
from .context_extraction_browser import extract_url_from_browser
from .context_extraction_outlook import extract_subject_from_outlook
from .context_extraction_office import extract_filepath_from_office
from .context_extraction_legal import extract_legal_context

def extract_context(app: str, title: str) -> str:
    """
    Extract contextual information from window title.

    Routes to appropriate extraction function:
    - Legal research → Citation/case name/docket extraction
    - Browsers → URL extraction
    - Outlook → Email subject extraction
    - Office apps → File path extraction

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted context string or None
    """
    if not app or not title:
        return None

    try:
        # Try legal research extraction first (highest value)
        legal = extract_legal_context(app, title)
        if legal:
            return legal

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
        logging.debug(f"Context extraction failed for {app}: {e}")
        return None
