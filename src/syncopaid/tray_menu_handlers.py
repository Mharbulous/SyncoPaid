"""
Menu handlers for the system tray icon.

Separated from main TrayIcon class to reduce file size.
"""

import logging
from syncopaid.tray_startup import is_startup_enabled, enable_startup, disable_startup

# Version info
try:
    from syncopaid import __product_version__
except ImportError:
    __product_version__ = "1.0.0"


class TrayMenuHandlers:
    """Mixin class providing menu handler methods for TrayIcon."""

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
