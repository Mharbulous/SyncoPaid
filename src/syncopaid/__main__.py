"""
SyncoPaid - Main entry point.

Coordinates all components:
- Configuration management
- Database initialization
- Tracking loop
- System tray UI
- Data export

This is the file that runs when you execute: python -m SyncoPaid
"""

import sys
import logging
import threading

from syncopaid.config import ConfigManager, print_config
from syncopaid.database import Database, format_duration
from syncopaid.tracker import TrackerLoop
from syncopaid.exporter import Exporter
from syncopaid.tray import TrayIcon, sync_startup_registry
from syncopaid.screenshot import ScreenshotWorker, get_screenshot_directory
from syncopaid.action_screenshot import ActionScreenshotWorker, get_action_screenshot_directory
from syncopaid.main_single_instance import acquire_single_instance, release_single_instance
from syncopaid.main_ui_windows import show_export_dialog, show_main_window


# Version info
try:
    from syncopaid import __product_version__
except ImportError:
    __product_version__ = "1.0.0"  # Fallback if not yet generated


class SyncoPaidApp:
    """
    Main application coordinator.
    
    Manages the lifecycle of all components and handles coordination
    between the tracking loop, database, and UI.
    """
    
    def __init__(self):
        """Initialize the application."""
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

        # Initialize database
        db_path = self.config_manager.get_database_path()
        self.database = Database(str(db_path))

        # Initialize exporter
        self.exporter = Exporter(self.database)

        # Initialize screenshot worker (if enabled)
        self.screenshot_worker = None
        if self.config.screenshot_enabled:
            screenshot_dir = get_screenshot_directory()
            self.screenshot_worker = ScreenshotWorker(
                screenshot_dir=screenshot_dir,
                db_insert_callback=self.database.insert_screenshot,
                threshold_identical=self.config.screenshot_threshold_identical,
                threshold_significant=self.config.screenshot_threshold_significant,
                threshold_identical_same_window=self.config.screenshot_threshold_identical_same_window,
                threshold_identical_different_window=self.config.screenshot_threshold_identical_different_window,
                quality=self.config.screenshot_quality,
                max_dimension=self.config.screenshot_max_dimension
            )
            logging.info("Screenshot worker initialized")

        # Initialize action screenshot worker (if enabled)
        self.action_screenshot_worker = None
        if self.config.action_screenshot_enabled:
            action_screenshot_dir = get_action_screenshot_directory()
            self.action_screenshot_worker = ActionScreenshotWorker(
                screenshot_dir=action_screenshot_dir,
                db_insert_callback=self.database.insert_screenshot,
                quality=self.config.action_screenshot_quality,
                max_dimension=self.config.action_screenshot_max_dimension,
                throttle_seconds=self.config.action_screenshot_throttle_seconds,
                enabled=True
            )
            logging.info("Action screenshot worker initialized")

        # Initialize tracker loop
        self.tracker = TrackerLoop(
            poll_interval=self.config.poll_interval_seconds,
            idle_threshold=self.config.idle_threshold_seconds,
            merge_threshold=self.config.merge_threshold_seconds,
            screenshot_worker=self.screenshot_worker,
            screenshot_interval=self.config.screenshot_interval_seconds,
            minimum_idle_duration=self.config.minimum_idle_duration_seconds
        )

        # Tracking state
        self.tracking_thread: threading.Thread = None
        self.is_tracking = False

        # System tray
        self.tray = TrayIcon(
            on_start=self.start_tracking,
            on_pause=self.pause_tracking,
            on_view_time=self.show_main_window,
            on_quit=self.quit_app,
            config_manager=self.config_manager
        )

        logging.info("SyncoPaid application initialized")
    
    def start_tracking(self):
        """Start the tracking loop in a background thread."""
        if self.is_tracking:
            logging.warning("Tracking already running")
            return

        self.is_tracking = True
        self.tracking_thread = threading.Thread(
            target=self._run_tracking_loop,
            daemon=True
        )
        self.tracking_thread.start()

        # Start action screenshot worker
        if self.action_screenshot_worker:
            self.action_screenshot_worker.start()

        logging.info("Tracking started")
        print("[OK] Tracking started")
    
    def pause_tracking(self):
        """Pause the tracking loop."""
        if not self.is_tracking:
            logging.warning("Tracking not running")
            return

        self.is_tracking = False
        self.tracker.stop()

        # Stop action screenshot worker
        if self.action_screenshot_worker:
            self.action_screenshot_worker.stop()

        logging.info("Tracking paused")
        print("[PAUSED] Tracking paused")
    
    def _run_tracking_loop(self):
        """
        Run the tracking loop and store events in database.
        
        This runs in a background thread and continuously captures
        activity events, storing them to the database.
        """
        logging.info("Tracking loop thread started")
        
        try:
            for event in self.tracker.start():
                # Store event in database
                event_id = self.database.insert_event(event)
                
                # Log to console (optional - can be disabled for production)
                if not event.is_idle:
                    logging.debug(
                        f"Captured: {event.app} - {event.title[:40]} "
                        f"({event.duration_seconds:.1f}s)"
                    )
        
        except Exception as e:
            logging.error(f"Error in tracking loop: {e}", exc_info=True)
        
        finally:
            logging.info("Tracking loop thread ended")
    
    def show_export_dialog(self):
        """Show dialog for exporting data."""
        show_export_dialog(self.exporter, self.database)

    def show_main_window(self):
        """Show main application window displaying activity from the past 24 hours."""
        show_main_window(self.database, self.tray, self.quit_app)

    def show_settings_dialog(self):
        """Show settings dialog."""
        # For MVP, just print current settings to console
        # Can be enhanced with a proper GUI later
        print("\n" + "="*60)
        print_config(self.config)
        print("\nTo modify settings, edit:")
        print(f"  {self.config_manager.config_path}")
        print("="*60 + "\n")
    
    def show_statistics(self):
        """Display database statistics."""
        stats = self.database.get_statistics()
        
        print("\n" + "="*60)
        print("SyncoPaid Statistics")
        print("="*60)
        print(f"Total events captured: {stats['total_events']}")
        print(f"Active time: {format_duration(stats['active_duration_seconds'])}")
        print(f"Idle time: {format_duration(stats['idle_duration_seconds'])}")
        
        if stats['first_event']:
            print(f"First event: {stats['first_event'][:19]}")
            print(f"Last event: {stats['last_event'][:19]}")
            print(f"Days tracked: {stats['date_range_days']}")
        
        print("="*60 + "\n")
    
    def quit_app(self):
        """Clean shutdown of the application."""
        logging.info("Application shutting down...")

        # Stop tracking
        if self.is_tracking:
            self.pause_tracking()

        # Shutdown screenshot worker
        if self.screenshot_worker:
            self.screenshot_worker.shutdown(wait=True, timeout=5.0)

        # Shutdown action screenshot worker
        if self.action_screenshot_worker:
            self.action_screenshot_worker.shutdown(wait=True, timeout=5.0)

        # Show final statistics
        self.show_statistics()

        # Release single-instance mutex
        release_single_instance()

        logging.info("Goodbye!")
        sys.exit(0)
    
    def run(self):
        """
        Run the application.

        This is the main entry point that starts everything.
        """
        logging.info("SyncoPaid starting...")

        # Sync "Start with Windows" registry to match config setting
        # This also migrates old SyncoPaid entries and updates exe path if moved
        sync_startup_registry(self.config.start_on_boot)

        # Show welcome message
        print("\n" + "="*60)
        print(f"SyncoPaid v{__product_version__}")
        print("Windows 11 automatic time tracking for lawyers")
        print("="*60)
        print(f"\nDatabase: {self.config_manager.get_database_path()}")
        print(f"Config: {self.config_manager.config_path}")
        print("="*60 + "\n")

        # Start tracking if configured to do so
        if self.config.start_tracking_on_launch:
            self.start_tracking()
            self.tray.update_icon_status(True)

        # Run system tray (this blocks until quit)
        self.tray.run()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the application."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Optionally add file handler
            # logging.FileHandler('lawtime.log')
        ]
    )

    # Enforce single instance
    if not acquire_single_instance():
        print("SyncoPaid is already running.")
        print("Check your system tray for the existing instance.")
        sys.exit(0)

    try:
        app = SyncoPaidApp()
        app.run()

    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        release_single_instance()
        sys.exit(0)

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        release_single_instance()
        sys.exit(1)


if __name__ == "__main__":
    main()
