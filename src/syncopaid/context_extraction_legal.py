"""Legal research context extraction from window titles."""
import re
from .context_extraction_browser import BROWSER_APPS

# Legal research platforms (desktop apps and browser patterns)
LEGAL_RESEARCH_APPS = {
    'westlaw.exe', 'westlawnext.exe', 'lexisnexis.exe',
    'fastcase.exe', 'casetext.exe'
}

LEGAL_RESEARCH_BROWSER_PATTERNS = [
    'westlaw', 'canlii', 'lexisnexis', 'lexis+',
    'fastcase', 'casetext', 'courtlistener', 'justia',
    'court'  # Generic court portals
]

# Canadian neutral citation pattern: YYYY CourtCode Number
# Examples: 2024 BCSC 1234, 2023 SCC 15, 2022 ONCA 456
CANADIAN_CITATION_PATTERN = re.compile(
    r'\b(20\d{2})\s+'  # Year (2000-2099)
    r'([A-Z]{2,6})\s+'  # Court code (2-6 uppercase letters)
    r'(\d{1,5})\b'       # Decision number
)

# Case name patterns: Party v. Party, In re X, Matter of X
CASE_NAME_PATTERN = re.compile(
    r'\b('
    r'[A-Z][a-zA-Z\'\-]+(?:\s+(?:of\s+)?[A-Z][a-zA-Z\'\-]+)*'  # First party (with "of")
    r'\s+v\.?\s+'                                               # "v" or "v."
    r'[A-Z][a-zA-Z\'\-]+(?:\s+(?:of\s+)?[A-Z][a-zA-Z\'\-]+)*'  # Second party (with "of")
    r'|'
    r'(?:In\s+re|Matter\s+of)\s+'                               # In re / Matter of
    r'[A-Z][a-zA-Z\'\-]+(?:\s+(?:of\s+)?[A-Z][a-zA-Z\'\-]+)*'  # Subject (with "of")
    r')\b'
)

# Docket/file number patterns
DOCKET_PATTERN = re.compile(
    r'(?:Case\s+No\.?|Docket:?|File\s+No\.?|Court\s+File\s+No\.?)\s*'
    r'([A-Z0-9\-:]+)',
    re.IGNORECASE
)

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

def extract_canadian_citation(title: str) -> str:
    """
    Extract Canadian neutral citation from window title.

    Examples: 2024 BCSC 1234, 2023 SCC 15, 2022 ONCA 456

    Args:
        title: Window title text

    Returns:
        Citation string (e.g., "2024 BCSC 1234") or None
    """
    if not title:
        return None

    match = CANADIAN_CITATION_PATTERN.search(title)
    if match:
        year, court, number = match.groups()
        return f"{year} {court} {number}"

    return None

def extract_case_name(title: str) -> str:
    """
    Extract US-style case name from window title.

    Examples: Smith v. Jones, In re Application of Smith

    Args:
        title: Window title text

    Returns:
        Case name string or None
    """
    if not title:
        return None

    # Handle "Re:" prefix separately (strip it from result)
    re_prefix_match = re.search(r'Re:\s*(Matter\s+of\s+[A-Z][a-zA-Z\'\-]+(?:\s+(?:of\s+)?[A-Z][a-zA-Z\'\-]+)*)', title)
    if re_prefix_match:
        return re_prefix_match.group(1).strip()

    match = CASE_NAME_PATTERN.search(title)
    if match:
        case_name = match.group(1).strip()
        # Clean up trailing punctuation
        case_name = re.sub(r'[\s\-]+$', '', case_name)
        return case_name if len(case_name) > 5 else None

    return None

def extract_docket_number(title: str) -> str:
    """
    Extract court docket/file number from window title.

    Examples: 2024-CV-12345, 1:24-cv-00123

    Args:
        title: Window title text

    Returns:
        Docket number string or None
    """
    if not title:
        return None

    match = DOCKET_PATTERN.search(title)
    if match:
        docket = match.group(1).strip()
        # Must have at least one digit to be a valid docket
        if re.search(r'\d', docket):
            return docket

    return None

def extract_legal_context(app: str, title: str) -> str:
    """
    Extract legal research context from window title.

    Combines multiple extraction strategies:
    1. Canadian neutral citations (2024 BCSC 1234)
    2. US case names (Smith v. Jones)
    3. Docket/file numbers (2024-CV-12345)

    Args:
        app: Application executable name
        title: Window title text

    Returns:
        Extracted legal context or None
    """
    if not is_legal_research_app(app, title):
        return None

    # Priority order: Citations > Case Names > Docket Numbers
    citation = extract_canadian_citation(title)
    if citation:
        return citation

    case_name = extract_case_name(title)
    if case_name:
        return case_name

    docket = extract_docket_number(title)
    if docket:
        return docket

    return None
