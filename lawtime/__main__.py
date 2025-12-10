"""
LawTime Tracker - Main entry point.

Coordinates all components:
- Configuration management
- Database initialization
- Tracking loop
- System tray UI
- Data export

This is the file that runs when you execute: python -m lawtime
"""

import sys
import os
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime, date, timedelta
import ctypes

from .config import ConfigManager, print_config
from .database import Database, format_duration
from .tracker import TrackerLoop
from .exporter import Exporter
from .tray import TrayIcon
from .screenshot import ScreenshotWorker, get_screenshot_directory
from .action_screenshot import ActionScreenshotWorker, get_action_screenshot_directory


# Single-instance enforcement using Windows mutex
_MUTEX_NAME = "LawTimeTracker_SingleInstance_Mutex"
_mutex_handle = None


def acquire_single_instance():
    """
    Acquire a Windows mutex to ensure only one instance runs.

    Returns:
        True if this is the only instance, False if another instance is running.
    """
    global _mutex_handle

    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183

    # Create named mutex
    _mutex_handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)

    # Check if mutex already existed
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        if _mutex_handle:
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
        return False

    return True


def release_single_instance():
    """Release the Windows mutex."""
    global _mutex_handle
    if _mutex_handle:
        ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None


class LawTimeApp:
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
            screenshot_interval=self.config.screenshot_interval_seconds
        )

        # Tracking state
        self.tracking_thread: threading.Thread = None
        self.is_tracking = False

        # System tray
        self.tray = TrayIcon(
            on_start=self.start_tracking,
            on_pause=self.pause_tracking,
            on_view_time=self.show_view_time_window,
            on_settings=self.show_settings_dialog,
            on_quit=self.quit_app
        )

        logging.info("LawTime application initialized")
    
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
        print("✓ Tracking started")
    
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
        print("⏸ Tracking paused")
    
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
        # Run tkinter dialog in a separate thread with its own event loop
        # to avoid blocking issues with pystray
        def run_dialog():
            try:
                # Create a new Tk instance for this dialog
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                root.attributes('-topmost', True)  # Bring to front
                root.focus_force()

                # Ask for output file
                output_path = filedialog.asksaveasfilename(
                    parent=root,
                    title="Export Activity Data",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialfile=f"lawtime_export_{datetime.now().strftime('%Y%m%d')}.json"
                )

                if output_path:
                    # Get date range (default: today)
                    today = date.today().isoformat()

                    # Simple dialog for date range (can be enhanced later)
                    # For MVP, just export today's data
                    result = self.exporter.export_to_json(
                        output_path=output_path,
                        start_date=today,
                        end_date=today,
                        include_idle=True
                    )

                    logging.info(f"Exported {result['events_exported']} events to {output_path}")

                    # Show success message
                    messagebox.showinfo(
                        "Export Successful",
                        f"Exported {result['events_exported']} events\n"
                        f"Total time: {result['total_duration_hours']} hours\n\n"
                        f"File: {output_path}",
                        parent=root
                    )

                root.destroy()

            except Exception as e:
                logging.error(f"Error exporting data: {e}", exc_info=True)
                try:
                    messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
                except:
                    print(f"Export error: {e}")

        # Run in thread to avoid blocking pystray
        dialog_thread = threading.Thread(target=run_dialog, daemon=True)
        dialog_thread.start()

    def show_view_time_window(self):
        """Show window displaying activity from the past 24 hours."""
        def run_window():
            try:
                # Query events from the past 24 hours
                cutoff = datetime.now() - timedelta(hours=24)
                cutoff_iso = cutoff.isoformat()

                # Get events directly with timestamp comparison
                events = []
                with self.database._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """SELECT * FROM events
                           WHERE timestamp >= ? AND is_idle = 0
                           ORDER BY timestamp DESC""",
                        (cutoff_iso,)
                    )
                    for row in cursor.fetchall():
                        events.append({
                            'timestamp': row['timestamp'],
                            'duration_seconds': row['duration_seconds'],
                            'app': row['app'],
                            'title': row['title'],
                        })

                # Create window
                root = tk.Tk()
                root.title("LawTime - Last 24 Hours")
                root.geometry("800x500")
                root.attributes('-topmost', True)

                # Header frame
                header = tk.Frame(root, pady=10)
                header.pack(fill=tk.X)

                # Calculate totals
                total_seconds = sum(e['duration_seconds'] for e in events)
                tk.Label(
                    header,
                    text=f"Activity: {format_duration(total_seconds)} ({len(events)} events)",
                    font=('Segoe UI', 12, 'bold')
                ).pack()

                # Treeview for events
                columns = ('time', 'duration', 'app', 'title')
                tree = ttk.Treeview(root, columns=columns, show='headings')
                tree.heading('time', text='Time')
                tree.heading('duration', text='Duration')
                tree.heading('app', text='Application')
                tree.heading('title', text='Window Title')

                tree.column('time', width=140, minwidth=100)
                tree.column('duration', width=70, minwidth=50)
                tree.column('app', width=120, minwidth=80)
                tree.column('title', width=450, minwidth=200)

                # Scrollbar
                scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)

                # Function to open screenshot directory
                def open_screenshot_folder():
                    """Open the screenshot directory in Windows Explorer."""
                    try:
                        screenshot_dir = get_screenshot_directory()
                        # Ensure the directory exists
                        screenshot_dir.mkdir(parents=True, exist_ok=True)
                        # Open in Windows Explorer
                        os.startfile(str(screenshot_dir))
                        logging.info(f"Opened screenshot directory: {screenshot_dir}")
                    except Exception as e:
                        logging.error(f"Error opening screenshot directory: {e}")
                        messagebox.showerror(
                            "Error",
                            f"Could not open screenshot directory:\n{str(e)}",
                            parent=root
                        )

                # Button frame - pack BEFORE treeview so it reserves space at top
                btn_frame = tk.Frame(root, pady=5)
                btn_frame.pack(fill=tk.X, side=tk.TOP)

                tk.Button(
                    btn_frame,
                    text="View Captured Images",
                    command=open_screenshot_folder,
                    width=20
                ).pack(side=tk.LEFT, padx=10)

                tk.Button(
                    btn_frame,
                    text="Close",
                    command=root.destroy,
                    width=10
                ).pack(side=tk.RIGHT, padx=10)

                # Pack treeview and scrollbar AFTER button frame
                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                # Insert events
                for event in events:
                    ts = event['timestamp'][:19].replace('T', ' ')
                    dur = format_duration(event['duration_seconds'])
                    app = event['app'] or ''
                    title = event['title'] or ''
                    tree.insert('', tk.END, values=(ts, dur, app, title))

                root.mainloop()

            except Exception as e:
                logging.error(f"Error showing view time window: {e}", exc_info=True)

        # Run in thread to avoid blocking pystray
        window_thread = threading.Thread(target=run_window, daemon=True)
        window_thread.start()

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
        print("LawTime Tracker Statistics")
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
        logging.info("LawTime Tracker starting...")
        
        # Show welcome message
        print("\n" + "="*60)
        print("LawTime Tracker v0.1.0")
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
        print("LawTime Tracker is already running.")
        print("Check your system tray for the existing instance.")
        sys.exit(0)

    try:
        app = LawTimeApp()
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
