"""Client and matter management dialogs.

This module re-exports classes from decomposed submodules for backward compatibility.
"""


def format_keywords_for_display(
    keywords: list,
    max_display: int = 5
) -> str:
    """
    Format keywords list for UI display.

    Args:
        keywords: List of keyword dicts with 'keyword' and 'confidence'
        max_display: Maximum keywords to show before truncating

    Returns:
        Comma-separated string of keywords, with "..." if truncated
    """
    if not keywords:
        return ""

    # Sort by confidence (should already be sorted, but ensure)
    sorted_kw = sorted(keywords, key=lambda k: k.get('confidence', 0), reverse=True)

    # Take top N keywords
    display_kw = [k['keyword'] for k in sorted_kw[:max_display]]

    # Add ellipsis if truncated
    if len(sorted_kw) > max_display:
        display_kw.append("...")

    return ", ".join(display_kw)


def get_matters_with_keywords(db) -> list:
    """
    Get all matters with their AI-extracted keywords formatted for display.

    Args:
        db: Database instance

    Returns:
        List of matter dicts with added 'keywords_display' field
    """
    matters = db.get_matters(status='all')

    for matter in matters:
        keywords = db.get_matter_keywords(matter['id'])
        matter['keywords_display'] = format_keywords_for_display(keywords)
        matter['keywords_raw'] = keywords  # For tooltip/detail view

    return matters


from syncopaid.matter_client_csv import export_matters_csv, import_matters_csv

# Import GUI classes only if tkinter is available (not in CI/testing environments)
try:
    from syncopaid.matter_client_dialog_clients import ClientDialog, ClientEditDialog
    from syncopaid.matter_client_dialog_matters import MatterDialog, MatterEditDialog
    _GUI_AVAILABLE = True
except ImportError:
    # Define dummy classes for testing environments
    ClientDialog = None
    ClientEditDialog = None
    MatterDialog = None
    MatterEditDialog = None
    _GUI_AVAILABLE = False

__all__ = [
    'export_matters_csv',
    'import_matters_csv',
    'ClientDialog',
    'ClientEditDialog',
    'MatterDialog',
    'MatterEditDialog',
    'format_keywords_for_display',
    'get_matters_with_keywords',
]
