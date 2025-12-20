"""
System tray UI module for SyncoPaid.

Provides a minimal system tray interface with:
- State-specific icons:
  - stopwatch-pictogram-green = tracking active
  - stopwatch-pictogram-orange = user manually paused (with ❚❚ overlay)
  - stopwatch-pictogram-faded = no activity for 5min (with 💤 overlay)
- Right-click menu with Start/Pause, Open SyncoPaid, Start with Windows, About
- Notifications for key events
"""

import logging
from typing import Callable, Optional

# Import helper modules
from syncopaid.tray_startup import (
    is_startup_enabled,
    enable_startup,
    disable_startup,
    sync_startup_registry
)
from syncopaid.tray_icons import create_icon_image, get_resource_path

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


class TrayIcon:
    """
    System tray icon manager.

    Provides a simple interface for controlling the tracker with three states:
    - stopwatch-pictogram-green = tracking active
    - stopwatch-pictogram-orange + ❚❚ overlay = user manually paused
    - stopwatch-pictogram-faded + 💤 overlay = no activity for 5min

    Menu options:
    - Start/Pause Tracking
    - Open SyncoPaid
    - Start with Windows
    - About
    - Quit
    """

    def __init__(
        self,
        on_start: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_open: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        config_manager=None
    ):
        """
        Initialize system tray icon.

        Args:
            on_start: Callback for "Start Tracking" menu item
            on_pause: Callback for "Pause Tracking" menu item
            on_open: Callback for "Open SyncoPaid" menu item
            on_quit: Callback for "Quit" menu item
            config_manager: ConfigManager instance for persisting settings
        """
        self.on_start = on_start or (lambda: None)
        self.on_pause = on_pause or (lambda: None)
        self.on_open = on_open or (lambda: None)
        self.on_quit = on_quit or (lambda: None)
        self.config_manager = config_manager

        self.icon: Optional[pystray.Icon] = None
        self.is_tracking = True
        self.is_inactive = False  # True when no activity for 5 minutes

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

    def _create_menu(self):
        """Create the right-click menu."""
        if not TRAY_AVAILABLE:
            return None

        return pystray.Menu(
            pystray.MenuItem(
                lambda text: "⏸ Pause Tracking" if self.is_tracking else "▶ Start Tracking",
                self._toggle_tracking,
                default=True
            ),
            pystray.MenuItem("📊 Open SyncoPaid", self._handle_open),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "🚀 Start with Windows",
                self._toggle_startup,
                checked=lambda item: is_startup_enabled()
            ),
            pystray.MenuItem("ℹ About", self._handle_about)
            # Quit option removed - use command field with "quit" command
        )

    def _toggle_tracking(self, icon, item):
        """Handle Start/Pause tracking menu item."""
        if self.is_tracking:
            logging.info("User paused tracking from tray menu")
            self.on_pause()
            self.is_tracking = False
        else:
            logging.info("User started tracking from tray menu")
            self.on_start()
            self.is_tracking = True
            self.is_inactive = False  # Clear inactive when user resumes

        self._refresh_icon()

    def _handle_open(self, icon, item):
        """Handle Open SyncoPaid menu item."""
        logging.info("User clicked Open SyncoPaid from tray menu")
        self.on_open()

    def _toggle_startup(self, icon, item):
        """Handle Start with Windows toggle."""
        current_state = is_startup_enabled()
        new_state = not current_state

        if new_state:
            # Enable startup
            success = enable_startup()
            if success:
                logging.info("User enabled startup from tray menu")
            else:
                logging.error("Failed to enable startup")
        else:
            # Disable startup
            success = disable_startup()
            if success:
                logging.info("User disabled startup from tray menu")
            else:
                logging.error("Failed to disable startup")

        # Save the setting to config so it persists
        if success and self.config_manager:
            self.config_manager.update(start_on_boot=new_state)
            logging.info(f"Saved start_on_boot={new_state} to config")

        # Force menu update to reflect new state
        if self.icon:
            self.icon.update_menu()

    def _handle_about(self, icon, item):
        """Handle About menu item."""
        logging.info("User clicked About from tray menu")
        # TODO: Show about dialog
        print("\n" + "="*50)
        print(f"SyncoPaid v{__product_version__}")
        print("Windows 11 automatic time tracking for lawyers")
        print("="*50 + "\n")

    def _handle_quit(self, icon, item):
        """Handle Quit menu item."""
        logging.info("User quit from tray menu")
        # Stop the tray icon first to release the event loop
        if self.icon:
            self.icon.stop()
        # Then run cleanup callback (which may call sys.exit)
        self.on_quit()

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

    def _run_console_fallback(self):
        """
        Fallback console interface when system tray is unavailable.

        Provides basic commands: start, pause, export, quit.
        """
        print("\n" + "="*60)
        print("SyncoPaid Tracker - Console Mode")
        print("(System tray not available)")
        print("="*60)
        print("\nCommands:")
        print("  start  - Start tracking")
        print("  pause  - Pause tracking")
        print("  open   - Open main window")
        print("  quit   - Quit application")
        print("\n")

        while True:
            try:
                cmd = input("SyncoPaid> ").strip().lower()

                if cmd == "start":
                    print("▶ Starting tracking...")
                    self.is_tracking = True
                    self.on_start()

                elif cmd == "pause":
                    print("⏸ Pausing tracking...")
                    self.is_tracking = False
                    self.on_pause()

                elif cmd == "open":
                    print("📊 Opening SyncoPaid...")
                    self.on_open()

                elif cmd == "quit" or cmd == "exit":
                    print("❌ Quitting...")
                    self.on_quit()
                    break

                else:
                    print(f"Unknown command: {cmd}")

            except (KeyboardInterrupt, EOFError):
                print("\n❌ Quitting...")
                self.on_quit()
                break

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

    # Create tray icon
    tray = TrayIcon(
        on_start=on_start,
        on_pause=on_pause,
        on_open=on_open,
        on_quit=on_quit
    )

    if TRAY_AVAILABLE:
        print("Starting system tray icon...")
        print("Right-click the icon in your system tray to test the menu.")
        print("Select 'Quit' to exit.\n")
        tray.run()
    else:
        print("⚠ pystray not available - starting console fallback...")
        tray.run()
