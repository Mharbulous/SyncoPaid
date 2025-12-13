"""
TimeLawg - Windows 11 automatic time tracking for legal professionals.

This package provides passive background capture of window activity, idle detection,
and data export for LLM-powered billing categorization.
"""

# Version info - generated at build time in timelawg/_version.py
try:
    from timelawg._version import __version__, __product_version__
except ImportError:
    # Fallback for development (when not built)
    __version__ = "0.0.0.dev"
    __product_version__ = "0.0.0"
__author__ = "Brahm Bhandari"
