"""
Core tracking module for capturing window activity and idle detection.

This module provides the TrackerLoop class which continuously monitors:
- Active window title and application
- User idle time (keyboard/mouse inactivity)
- Event merging to combine consecutive identical activities

All data is captured locally at second-level precision.
"""

import re
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Generator
from dataclasses import dataclass, asdict

# Platform detection
import sys
WINDOWS = sys.platform == 'win32'

if WINDOWS:
    try:
        import win32gui
        import win32process
        import psutil
        from ctypes import Structure, windll, c_uint, sizeof, byref
        WINDOWS_APIS_AVAILABLE = True
    except ImportError:
        WINDOWS_APIS_AVAILABLE = False
        logging.warning("Windows APIs not available. Install pywin32 and psutil.")
else:
    WINDOWS_APIS_AVAILABLE = False


# ============================================================================
# STATE CONSTANTS AND VALIDATION
# ============================================================================

# System states (assigned automatically based on tracking conditions)
STATE_ACTIVE = "Active"       # Tracked activity, client matter TBD (default)
STATE_INACTIVE = "Inactive"   # Idle detected (keyboard/mouse inactivity)
STATE_OFF = "Off"             # TimeLawg wasn't running (gaps)
STATE_BLOCKED = "Blocked"     # Auto-blocked content (passwords, incognito)
STATE_PAUSED = "Paused"       # User manually paused tracking

# User-assigned states (non-billable)
STATE_PERSONAL = "Personal"   # Personal time
STATE_ON_BREAK = "On-break"   # Break time

# States that can be converted to client matters
CONVERTIBLE_STATES = {STATE_ACTIVE, STATE_INACTIVE, STATE_OFF}

# All valid system/user states
VALID_STATES = {
    STATE_ACTIVE, STATE_INACTIVE, STATE_OFF, STATE_BLOCKED,
    STATE_PAUSED, STATE_PERSONAL, STATE_ON_BREAK
}

# Client matter pattern: 4 digits, dot, optional letter, 3 digits
# Examples: 1023.L213, 1214.001
CLIENT_MATTER_PATTERN = re.compile(r'^\d{4}\.[A-Z]?\d{3}$')


def is_valid_state(state: str) -> bool:
    """Check if state is valid (system state or client matter number)."""
    if state in VALID_STATES:
        return True
    return bool(CLIENT_MATTER_PATTERN.match(state))


def is_client_matter(state: str) -> bool:
    """Check if state is a client matter number (not a system state)."""
    return bool(CLIENT_MATTER_PATTERN.match(state))


def can_convert_to_matter(state: str) -> bool:
    """Check if a state can be converted to a client matter number."""
    return state in CONVERTIBLE_STATES


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ActivityEvent:
    """
    Represents a single captured activity event.

    This is the core data structure that will be stored in the database
    and exported for LLM processing.

    Fields:
        timestamp: Start time in ISO8601 format (e.g., "2025-12-09T10:30:45")
        duration_seconds: Duration in seconds (may be None for legacy records)
        end_time: End time in ISO8601 format (may be None for legacy records)
        app: Application executable name
        title: Window title
        url: URL if applicable (future enhancement)
        is_idle: Whether this was an idle period (deprecated - use state)
        state: Activity state or client matter number (e.g., "Active", "1023.L213")
    """
    timestamp: str  # ISO8601 format: "2025-12-09T10:30:45" (start time)
    duration_seconds: Optional[float]
    app: Optional[str]
    title: Optional[str]
    end_time: Optional[str] = None  # ISO8601 format (end time)
    url: Optional[str] = None
    is_idle: bool = False
    state: str = STATE_ACTIVE  # Default to Active (client matter TBD)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export or database storage."""
        return asdict(self)


# ============================================================================
# WINDOWS API FUNCTIONS
# ============================================================================

if WINDOWS_APIS_AVAILABLE:
    class LASTINPUTINFO(Structure):
        """Windows structure for GetLastInputInfo API."""
        _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]


def get_active_window() -> Dict[str, Optional[str]]:
    """
    Get information about the currently active foreground window.
    
    Returns:
        Dictionary with keys:
        - 'app': Executable name (e.g., 'WINWORD.EXE', 'chrome.exe')
        - 'title': Window title text
        - 'pid': Process ID (for debugging)
    
    Note: Returns mock data on non-Windows platforms for testing.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock data for testing on non-Windows platforms
        import random
        mock_apps = [
            ("WINWORD.EXE", "Smith-Contract-v2.docx - Word"),
            ("chrome.exe", "CanLII - 2024 BCSC 1234 - Google Chrome"),
            ("OUTLOOK.EXE", "Inbox - user@lawfirm.com - Outlook"),
        ]
        app, title = random.choice(mock_apps)
        return {"app": app, "title": title, "pid": 0}
    
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Handle signed/unsigned integer overflow from Windows API
        # Windows returns unsigned 32-bit PID, but Python may interpret as signed
        if pid < 0:
            pid = pid & 0xFFFFFFFF  # Convert to unsigned

        try:
            process = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            process = None

        return {"app": process, "title": title, "pid": pid}
    
    except Exception as e:
        logging.error(f"Error getting active window: {e}")
        return {"app": None, "title": None, "pid": None}


def get_idle_seconds() -> float:
    """
    Get the number of seconds since the last keyboard or mouse input.
    
    Uses Windows GetLastInputInfo API to detect user inactivity.
    
    Returns:
        Float representing idle seconds. Returns 0.0 on non-Windows platforms.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock: alternate between active (0s) and occasionally idle
        import random
        return random.choice([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 200.0])
    
    try:
        info = LASTINPUTINFO()
        info.cbSize = sizeof(info)
        windll.user32.GetLastInputInfo(byref(info))
        millis = windll.kernel32.GetTickCount() - info.dwTime
        return millis / 1000.0
    
    except Exception as e:
        logging.error(f"Error getting idle time: {e}")
        return 0.0


# ============================================================================
# TRACKER LOOP
# ============================================================================

class TrackerLoop:
    """
    Main tracking loop that captures window activity and generates events.

    This class manages the core tracking logic:
    - Polls active window at configurable interval
    - Detects idle periods
    - Merges consecutive identical activities
    - Yields ActivityEvent objects for storage
    - Submits periodic screenshots (if enabled)

    Configuration:
        poll_interval: How often to check active window (seconds)
        idle_threshold: Seconds before marking as idle
        merge_threshold: Max gap to merge identical windows (seconds)
        screenshot_worker: Optional ScreenshotWorker for capturing screenshots
        screenshot_interval: Seconds between screenshot attempts
    """

    def __init__(
        self,
        poll_interval: float = 1.0,
        idle_threshold: float = 180.0,
        merge_threshold: float = 2.0,
        screenshot_worker=None,
        screenshot_interval: float = 10.0
    ):
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.merge_threshold = merge_threshold
        self.screenshot_worker = screenshot_worker
        self.screenshot_interval = screenshot_interval

        # State tracking for event merging
        self.current_event: Optional[Dict] = None
        self.event_start_time: Optional[datetime] = None

        # Screenshot timing
        self.last_screenshot_time: float = 0

        self.running = False

        # Statistics
        self.total_events = 0
        self.merged_events = 0

        logging.info(
            f"TrackerLoop initialized: "
            f"poll={poll_interval}s, idle_threshold={idle_threshold}s, "
            f"merge_threshold={merge_threshold}s, "
            f"screenshot_enabled={screenshot_worker is not None}"
        )
    
    def start(self) -> Generator[ActivityEvent, None, None]:
        """
        Start the tracking loop.

        Yields:
            ActivityEvent objects when activities change or complete.

        This is a generator that runs indefinitely until stop() is called.
        Each yielded event is ready to be stored in the database.
        """
        self.running = True
        logging.info("Tracking started")

        while self.running:
            try:
                # Get current state
                window = get_active_window()
                idle_seconds = get_idle_seconds()
                is_idle = idle_seconds >= self.idle_threshold

                # Create state dict for comparison
                state = {
                    'app': window['app'],
                    'title': window['title'],
                    'is_idle': is_idle
                }

                # Submit screenshot if enabled and interval elapsed
                # Note: We only check if screenshot_worker exists. The worker itself
                # handles platform-specific checks (WINDOWS_APIS_AVAILABLE) internally.
                if self.screenshot_worker:
                    current_time = time.time()
                    time_since_last = current_time - self.last_screenshot_time

                    # Log diagnostic info on first screenshot attempt
                    if not hasattr(self, '_screenshot_diagnostic_logged'):
                        logging.info(
                            f"Screenshot capture enabled: interval={self.screenshot_interval}s, "
                            f"tracker_apis_available={WINDOWS_APIS_AVAILABLE}"
                        )
                        self._screenshot_diagnostic_logged = True

                    if time_since_last >= self.screenshot_interval:
                        logging.debug(f"Triggering screenshot capture (elapsed: {time_since_last:.1f}s)")
                        self._submit_screenshot(window, idle_seconds)
                        self.last_screenshot_time = current_time

                # Check if state changed
                if self._has_state_changed(state):
                    # Yield the completed event (if any)
                    if self.current_event is not None:
                        completed_event = self._finalize_current_event()
                        if completed_event:
                            yield completed_event

                    # Start new event
                    self.current_event = state
                    self.event_start_time = datetime.now(timezone.utc)

                # Sleep until next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                logging.error(f"Error in tracking loop: {e}")
                time.sleep(self.poll_interval)

        # Yield final event when stopped
        if self.current_event is not None:
            completed_event = self._finalize_current_event()
            if completed_event:
                yield completed_event

        logging.info(
            f"Tracking stopped. Total events: {self.total_events}, "
            f"Merged: {self.merged_events}"
        )
    
    def stop(self):
        """Stop the tracking loop."""
        self.running = False
    
    def _has_state_changed(self, new_state: Dict) -> bool:
        """
        Check if the current state is different from the tracked state.
        
        Considers the merge_threshold: if user briefly switches windows
        but returns within merge_threshold seconds, treat as continuous.
        """
        if self.current_event is None:
            return True
        
        # Check if core attributes changed
        if (new_state['app'] != self.current_event['app'] or
            new_state['title'] != self.current_event['title'] or
            new_state['is_idle'] != self.current_event['is_idle']):
            
            # State changed - check if within merge threshold
            if self.event_start_time:
                elapsed = (datetime.now(timezone.utc) - self.event_start_time).total_seconds()
                if elapsed < self.merge_threshold:
                    # Too quick - might be accidental switch, merge it
                    self.merged_events += 1
                    return False
            
            return True
        
        return False
    
    def _finalize_current_event(self) -> Optional[ActivityEvent]:
        """
        Convert the current tracked event into an ActivityEvent object.

        Returns None if the event is too short or invalid.
        """
        if not self.current_event or not self.event_start_time:
            return None

        # Calculate duration and end time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.event_start_time).total_seconds()

        # Skip events that are too short (< 0.5 seconds)
        if duration < 0.5:
            return None

        # Derive state from is_idle flag
        event_state = STATE_INACTIVE if self.current_event['is_idle'] else STATE_ACTIVE

        # Create event with start time, duration, end time, and state
        event = ActivityEvent(
            timestamp=self.event_start_time.isoformat(),
            duration_seconds=round(duration, 2),
            app=self.current_event['app'],
            title=self.current_event['title'],
            end_time=end_time.isoformat(),
            url=None,  # URL extraction is future enhancement
            is_idle=self.current_event['is_idle'],
            state=event_state
        )

        self.total_events += 1
        return event

    def _submit_screenshot(self, window: Dict, idle_seconds: float):
        """
        Submit a screenshot capture request to the worker.

        Args:
            window: Window information dict from get_active_window()
            idle_seconds: Current idle time
        """
        if not WINDOWS_APIS_AVAILABLE:
            # Log this once per session to inform user why screenshots aren't working
            if not hasattr(self, '_screenshot_platform_warning_logged'):
                logging.warning(
                    "Cannot capture screenshots: Windows APIs not available. "
                    "This is expected on non-Windows platforms or if pywin32/psutil are not installed."
                )
                self._screenshot_platform_warning_logged = True
            return

        try:
            # Get window handle
            hwnd = win32gui.GetForegroundWindow()
            timestamp = datetime.now().astimezone().isoformat()

            # Submit to worker (non-blocking)
            logging.debug(f"Submitting screenshot for {window['app']}")
            self.screenshot_worker.submit(
                hwnd=hwnd,
                timestamp=timestamp,
                window_app=window['app'],
                window_title=window['title'],
                idle_seconds=idle_seconds
            )

        except Exception as e:
            logging.error(f"Error submitting screenshot: {e}", exc_info=True)


# ============================================================================
# CONSOLE TEST MODE
# ============================================================================

def run_console_test(duration_seconds: int = 30):
    """
    Run tracker in console test mode for demonstration/debugging.
    
    Args:
        duration_seconds: How long to run the test (default 30s)
    """
    print("=" * 70)
    print("LawTime Tracker - Console Test Mode")
    print("=" * 70)
    print(f"Running for {duration_seconds} seconds...")
    print("Switch between windows to see tracking in action.\n")
    
    if not WINDOWS_APIS_AVAILABLE:
        print("⚠ Warning: Running with MOCK DATA (not on Windows)\n")
    
    tracker = TrackerLoop(
        poll_interval=1.0,
        idle_threshold=180.0,
        merge_threshold=2.0
    )
    
    events = []
    start_time = time.time()
    
    print(f"{'Timestamp':<20} {'Duration':<10} {'App':<20} {'Title':<40}")
    print("-" * 90)
    
    try:
        for event in tracker.start():
            # Store event
            events.append(event)
            
            # Display event
            ts = event.timestamp.split('T')[1][:8]  # Just show time
            status = "💤 IDLE" if event.is_idle else "✓"
            print(
                f"{ts:<20} "
                f"{event.duration_seconds:>6.1f}s   "
                f"{(event.app or 'unknown')[:18]:<20} "
                f"{(event.title or 'untitled')[:38]:<40}"
            )
            
            # Check if duration exceeded
            if time.time() - start_time >= duration_seconds:
                tracker.stop()
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        tracker.stop()
    
    # Summary
    print("\n" + "=" * 70)
    print(f"Test complete: {len(events)} events captured")
    print(f"Total active time: {sum(e.duration_seconds for e in events if not e.is_idle):.1f}s")
    print(f"Total idle time: {sum(e.duration_seconds for e in events if e.is_idle):.1f}s")
    print(f"Events merged: {tracker.merged_events}")
    print("=" * 70)
    
    return events


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run console test
    run_console_test(duration_seconds=30)
