"""Browser URL extraction using UI Automation."""
import logging
from typing import Optional

try:
    from pywinauto import Desktop
    from pywinauto.timings import Timings
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False

logger = logging.getLogger(__name__)

BROWSER_CONFIG = {
    "chrome.exe": {"control_type": "Edit", "class_name": "Chrome_OmniboxView"},
    "msedge.exe": {"control_type": "Edit", "class_name": "Chrome_OmniboxView"},
    "firefox.exe": {"control_type": "Edit", "class_name": "MozillaWindowClass"},
}

def extract_browser_url(app_name: str, timeout_ms: int = 100) -> Optional[str]:
    """
    Extract URL from browser address bar using UI Automation.

    Args:
        app_name: Browser executable name (e.g., "chrome.exe")
        timeout_ms: Max time to wait for extraction (default 100ms)

    Returns:
        URL string if successful, None otherwise
    """
    if not PYWINAUTO_AVAILABLE:
        logger.debug("pywinauto not available, skipping URL extraction")
        return None

    if app_name.lower() not in BROWSER_CONFIG:
        return None

    try:
        # Set timeout
        original_timeout = Timings.after_click_input_idle
        Timings.after_click_input_idle = timeout_ms / 1000.0

        config = BROWSER_CONFIG[app_name.lower()]
        desktop = Desktop(backend="uia")

        # Find active window
        window = desktop.top_window()

        # Find address bar control
        address_bar = window.child_window(
            control_type=config["control_type"],
            class_name=config["class_name"]
        )

        url = address_bar.get_value()

        # Restore timeout
        Timings.after_click_input_idle = original_timeout

        return url if url else None

    except Exception as e:
        logger.debug(f"Failed to extract URL from {app_name}: {e}")
        return None
