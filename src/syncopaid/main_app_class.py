"""
SyncoPaid - Main application class.

Coordinates all components:
- Configuration management
- Database initialization
- Tracking loop
- System tray UI
- Data export
"""

import sys
import logging
import threading

from syncopaid.config import ConfigManager
from syncopaid.database import Database
from syncopaid.exporter import Exporter
from syncopaid.tray import TrayIcon, sync_startup_registry
from syncopaid.main_single_instance import release_single_instance
from syncopaid.resource_monitor import ResourceMonitor
from syncopaid.main_app_initialization import (
    initialize_screenshot_worker,
    initialize_action_screenshot_worker,
    initialize_archiver,
    initialize_transition_detector,
    initialize_activity_matcher,
    initialize_tracker_loop
)
from syncopaid.main_app_tracking import start_tracking, pause_tracking
from syncopaid.main_app_display import (
    show_export_dialog_wrapper,
    show_main_window_wrapper,
    show_settings_dialog,
    show_statistics
)


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

        # Initialize resource monitor (before screenshot worker and tracker loop)
        self.resource_monitor = ResourceMonitor(
            cpu_threshold=self.config.resource_cpu_threshold,
            memory_threshold_mb=self.config.resource_memory_threshold_mb,
            battery_threshold=self.config.resource_battery_threshold,
            monitoring_interval_seconds=self.config.resource_monitoring_interval_seconds
        )
        logging.info("Resource monitor initialized")

        # Initialize screenshot worker (if enabled)
        self.screenshot_worker = initialize_screenshot_worker(self.config, self.database, self.resource_monitor)

        # Initialize action screenshot worker (if enabled)
        self.action_screenshot_worker = initialize_action_screenshot_worker(self.config, self.database)

        # Initialize archiver
        self.archiver = initialize_archiver()

        # Initialize transition detector (if enabled)
        self.transition_detector = initialize_transition_detector(self.config)

        # Initialize activity matcher (for categorization)
        self.matcher = initialize_activity_matcher(self.database, self.config)

        # Initialize tracker loop
        self.tracker = initialize_tracker_loop(
            self.config,
            self.screenshot_worker,
            self.transition_detector,
            self.database,
            self.resource_monitor
        )

        # Tracking state
        self.tracking_thread: threading.Thread = None
        self.is_tracking = False

        # System tray
        self.tray = TrayIcon(
            on_start=self.start_tracking,
            on_pause=self.pause_tracking,
            on_open=self.show_main_window,
            on_quit=self.quit_app,
            config_manager=self.config_manager
        )

        logging.info("SyncoPaid application initialized")

    def start_tracking(self):
        """Start the tracking loop in a background thread."""
        start_tracking(self)

    def pause_tracking(self):
        """Pause the tracking loop."""
        pause_tracking(self)

    def show_export_dialog(self):
        """Show dialog for exporting data."""
        show_export_dialog_wrapper(self)

    def show_main_window(self):
        """Show main application window displaying activity from the past 24 hours."""
        show_main_window_wrapper(self)

    def show_settings_dialog(self):
        """Show settings dialog."""
        show_settings_dialog(self)

    def show_statistics(self):
        """Display database statistics."""
        show_statistics(self)

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

        # Log resource statistics
        if self.resource_monitor:
            stats = self.resource_monitor.get_statistics()
            if stats['samples_count'] > 0:
                logging.info(
                    f"Resource stats - Peak CPU: {stats['peak_cpu']:.1f}%, "
                    f"Avg CPU: {stats['avg_cpu']:.1f}%, "
                    f"Peak Memory: {stats['peak_memory_mb']:.1f}MB, "
                    f"Avg Memory: {stats['avg_memory_mb']:.1f}MB"
                )

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
