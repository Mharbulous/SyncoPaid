"""
UI Automation module for extracting rich context from applications.
"""
import logging
from typing import Dict, Optional
from abc import ABC, abstractmethod
import sys

WINDOWS = sys.platform == 'win32'

if WINDOWS:
    try:
        import pywinauto
        from pywinauto import Application
        from pywinauto.timings import TimeoutError
        PYWINAUTO_AVAILABLE = True
    except ImportError:
        PYWINAUTO_AVAILABLE = False
else:
    PYWINAUTO_AVAILABLE = False


class BaseExtractor(ABC):
    """Base class for UI automation extractors."""

    def __init__(self, timeout_ms: int = 100):
        self.timeout_ms = timeout_ms

    @abstractmethod
    def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
        pass


class OutlookExtractor(BaseExtractor):
    """Extract email subject and sender from Outlook (Legacy)."""

    def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
        if not PYWINAUTO_AVAILABLE:
            return None
        if 'OUTLOOK' not in window_info.get('app', '').upper():
            return None
        # Stub - actual implementation in sub-plan 031
        logging.debug(f"Outlook extraction not yet implemented")
        return None


class ExplorerExtractor(BaseExtractor):
    """Extract current folder path from Windows Explorer."""

    def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
        if not PYWINAUTO_AVAILABLE:
            return None
        if 'explorer' not in window_info.get('app', '').lower():
            return None
        # Stub - actual implementation in sub-plan 032
        logging.debug(f"Explorer extraction not yet implemented")
        return None


class UIAutomationWorker:
    """Coordinates UI automation extraction across applications."""

    def __init__(self, enabled=True, outlook_enabled=True, explorer_enabled=True):
        self.enabled = enabled
        self.outlook_extractor = OutlookExtractor() if outlook_enabled else None
        self.explorer_extractor = ExplorerExtractor() if explorer_enabled else None

    def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
        if not self.enabled:
            return None

        app = window_info.get('app', '').upper()

        if self.outlook_extractor and 'OUTLOOK' in app:
            return self.outlook_extractor.extract(window_info)

        if self.explorer_extractor and 'EXPLORER' in app:
            return self.explorer_extractor.extract(window_info)

        return None
