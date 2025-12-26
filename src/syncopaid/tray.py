"""
System tray UI module for SyncoPaid.

The system tray is the primary entry point for all user interactions.

Status Icons:
- Green (stopwatch-pictogram-green) = Tracking Active
- Orange (stopwatch-paused + ❚❚) = Paused
- Faded (stopwatch-pictogram-faded + 💤) = Idle (5+ min no activity)

Interactions:
- Left-click: Records a time marker (task transition/interruption)
  - Brief visual feedback: icon flashes orange for 1 second
- Right-click menu:
  - Start/Pause: Toggle tracking without opening window
  - Open SyncoPaid: Opens Main Window
  - Quit: Exit app completely
"""

import logging
import threading
from typing import Callable, Optional

# Import helper modules
from syncopaid.tray_startup import sync_startup_registry
from syncopaid.tray_icons import create_icon_image
from syncopaid.tray_menu_handlers import TrayMenuHandlers
from syncopaid.tray_console_fallback import TrayConsoleFallback

# Version info
try:
    from syncopaid import __product_version__
except ImportError:
    __product_version__ = "1.0.0"  # Fallback if not yet generated

try:
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logging.warning("pystray not available. Install with: pip install pystray Pillow")


class TrayIcon(TrayMenuHandlers, TrayConsoleFallback):
    """
    System tray icon manager - primary entry point for user interactions.

    Status icons (three states):
    - Green = Tracking Active
    - Orange = Paused (user manually paused)
    - Faded = Idle (no activity for 5+ minutes)

    Interactions:
    - Left-click: Records a time marker (task transition/interruption)
      with visual feedback (icon flashes orange for 1 second)
    - Right-click menu:
      - Start/Pause: Toggle tracking (no window)
      - Open SyncoPaid: Opens Main Window
      - Quit: Exit app completely
    """

    def __init__(
        self,
        on_start: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_open: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        on_time_marker: Optional[Callable] = None,
        config_manager=None
    ):
        """
        Initialize system tray icon.

        Args:
            on_start: Callback for "Start Tracking" menu item
            on_pause: Callback for "Pause Tracking" menu item
            on_open: Callback for "Open SyncoPaid" menu item
            on_quit: Callback for "Quit" menu item
            on_time_marker: Callback for left-click time marker recording
            config_manager: ConfigManager instance for persisting settings
        """
        self.on_start = on_start or (lambda: None)
        self.on_pause = on_pause or (lambda: None)
        self.on_open = on_open or (lambda: None)
        self.on_quit = on_quit or (lambda: None)
        self.on_time_marker = on_time_marker or (lambda: None)
        self.config_manager = config_manager

        self.icon: Optional[pystray.Icon] = None
        self.is_tracking = True
        self.is_inactive = False  # True when no activity for 5 minutes
        self._feedback_in_progress = False  # Prevent overlapping feedback

        if not TRAY_AVAILABLE:
            logging.error("System tray not available - pystray not installed")

    def _get_current_state(self) -> str:
        """Get the current icon state based on tracking and inactive flags."""
        if not self.is_tracking:
            return "paused"
        elif self.is_inactive:
            return "inactive"
        else:
            return "on"

    def update_icon_status(self, is_tracking: bool):
        """
        Update icon based on tracking status (user pause/unpause).

        Args:
            is_tracking: True if tracking, False if user paused
        """
        self.is_tracking = is_tracking
        if is_tracking:
            self.is_inactive = False  # Clear inactive when user resumes

        self._refresh_icon()

    def set_inactive(self, inactive: bool):
        """
        Set inactive state (no activity detected for 5 minutes).

        This shows the faded icon with sleep emoji. Only applies when
        is_tracking is True (user hasn't manually paused).

        Args:
            inactive: True if no activity detected, False when activity resumes
        """
        if self.is_inactive != inactive:
            self.is_inactive = inactive
            if self.is_tracking:  # Only update if not manually paused
                self._refresh_icon()
                if inactive:
                    logging.info("User inactive - showing sleep icon")
                else:
                    logging.info("User active - showing normal icon")

    def _refresh_icon(self):
        """Refresh the icon based on current state."""
        if self.icon:
            state = self._get_current_state()
            self.icon.icon = create_icon_image(state)
            # Update tooltip to reflect state
            if state == "paused":
                self.icon.title = f"SyncoPaid v{__product_version__} - Paused"
            elif state == "inactive":
                self.icon.title = f"SyncoPaid v{__product_version__} - Inactive"
            else:
                self.icon.title = f"SyncoPaid v{__product_version__}"

    def _record_time_marker(self, icon=None, item=None):
        """
        Handle left-click: record a time marker with visual feedback.

        This records a task transition/interruption timestamp and provides
        brief visual feedback (icon flashes orange for 1 second).
        """
        # Prevent overlapping feedback animations
        if self._feedback_in_progress:
            return

        self._feedback_in_progress = True
        logging.info("User recorded time marker via left-click")

        try:
            # Call the time marker callback to record in database
            self.on_time_marker()

            # Show visual feedback: flash orange icon for 1 second
            if self.icon:
                # Save current state to restore later
                original_state = self._get_current_state()

                # Show plain orange icon as feedback
                self.icon.icon = create_icon_image("marker_feedback")

                # Schedule icon reset after 1 second
                def reset_icon():
                    try:
                        if self.icon:
                            self.icon.icon = create_icon_image(original_state)
                    except Exception as e:
                        logging.debug(f"Error resetting icon: {e}")
                    finally:
                        self._feedback_in_progress = False

                timer = threading.Timer(1.0, reset_icon)
                timer.daemon = True
                timer.start()
            else:
                self._feedback_in_progress = False

        except Exception as e:
            logging.error(f"Error recording time marker: {e}", exc_info=True)
            self._feedback_in_progress = False

    def _create_menu(self):
        """
        Create the right-click menu.

        Menu structure:
        - Start/Pause: Toggle tracking without opening window
        - Open SyncoPaid: Opens main window
        - Quit: Exit app completely

        Note: Left-click records a time marker (handled via default=True
        on a hidden menu item).
        """
        if not TRAY_AVAILABLE:
            return None

        return pystray.Menu(
            # Hidden default item for left-click - records time marker
            pystray.MenuItem(
                "Record Time Marker",
                self._record_time_marker,
                default=True,
                visible=False
            ),
            pystray.MenuItem(
                lambda text: "⏸ Pause" if self.is_tracking else "▶ Start",
                self._toggle_tracking
            ),
            pystray.MenuItem(
                "📊 Open SyncoPaid",
                self._handle_open
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕ Quit", self._handle_quit)
        )

    def run(self):
        """
        Start the system tray icon.

        This is a blocking call that runs the tray icon event loop.
        Should be called from the main thread.
        """
        if not TRAY_AVAILABLE:
            logging.error("Cannot run system tray - pystray not available")
            # Fallback: run a simple console interface
            self._run_console_fallback()
            return

        self.icon = pystray.Icon(
            "SyncoPaid_tracker",
            create_icon_image(self._get_current_state()),
            f"SyncoPaid v{__product_version__}",
            menu=self._create_menu()
        )

        logging.info("System tray icon starting...")
        self.icon.run()

    def stop(self):
        """Stop the system tray icon."""
        if self.icon:
            self.icon.stop()


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    import time

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Testing TrayIcon...\n")

    # Test callbacks
    def on_start():
        print("✓ Start callback triggered")

    def on_pause():
        print("✓ Pause callback triggered")

    def on_open():
        print("✓ Open callback triggered")
        print("  (In real app: would open main window)")

    def on_quit():
        print("✓ Quit callback triggered")
        print("  (In real app: would clean up and exit)")

    def on_time_marker():
        from datetime import datetime
        print(f"✓ Time marker recorded at {datetime.now().strftime('%H:%M:%S')}")
        print("  (In real app: would save to database)")

    # Create tray icon
    tray = TrayIcon(
        on_start=on_start,
        on_pause=on_pause,
        on_open=on_open,
        on_quit=on_quit,
        on_time_marker=on_time_marker
    )

    if TRAY_AVAILABLE:
        print("Starting system tray icon...")
        print("Left-click the icon to record a time marker.")
        print("Right-click the icon to see the menu.")
        print("Select 'Quit' to exit.\n")
        tray.run()
    else:
        print("⚠ pystray not available - starting console fallback...")
        tray.run()
