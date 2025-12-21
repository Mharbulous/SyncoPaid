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

        pid = window_info.get('pid')
        if not pid:
            return None

        try:
            app = Application(backend='uia').connect(
                process=pid, timeout=self.timeout_ms / 1000.0
            )
            main_window = app.window(pid=pid)

            # Try to find subject field
            subject_text = None
            try:
                subject_elem = main_window.child_window(
                    auto_id="Subject", control_type="Edit"
                )
                subject_text = subject_elem.window_text()
            except Exception:
                try:
                    subject_elem = main_window.child_window(
                        class_name="_WwG", found_index=0
                    )
                    subject_text = subject_elem.window_text()
                except Exception:
                    pass

            # Try to find sender field
            sender_text = None
            try:
                sender_elem = main_window.child_window(
                    auto_id="From", control_type="Edit"
                )
                sender_text = sender_elem.window_text()
            except Exception:
                pass

            if subject_text:
                result = {'email_subject': subject_text}
                if sender_text:
                    result['sender'] = sender_text
                return result

            return None

        except TimeoutError:
            logging.debug(f"Outlook extraction timeout after {self.timeout_ms}ms")
            return None
        except Exception as e:
            logging.debug(f"Outlook extraction failed: {e}")
            return None


class ExplorerExtractor(BaseExtractor):
    """Extract current folder path from Windows Explorer."""

    def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
        if not PYWINAUTO_AVAILABLE:
            return None

        if 'explorer' not in window_info.get('app', '').lower():
            return None

        pid = window_info.get('pid')
        if not pid:
            return None

        try:
            app = Application(backend='uia').connect(
                process=pid, timeout=self.timeout_ms / 1000.0
            )
            main_window = app.window(pid=pid)

            folder_path = None
            try:
                # AutomationId "41477" is standard for Explorer address bar
                address_bar = main_window.child_window(
                    auto_id="41477", control_type="Edit"
                )
                folder_path = address_bar.window_text()
            except Exception:
                try:
                    address_bar = main_window.child_window(
                        control_type="Edit", class_name="Edit", found_index=0
                    )
                    folder_path = address_bar.window_text()
                except Exception:
                    pass

            if folder_path:
                return {'folder_path': folder_path}

            return None

        except TimeoutError:
            logging.debug(f"Explorer extraction timeout after {self.timeout_ms}ms")
            return None
        except Exception as e:
            logging.debug(f"Explorer extraction failed: {e}")
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
