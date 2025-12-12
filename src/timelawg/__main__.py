"""
LawTime Tracker - Main entry point.

Coordinates all components:
- Configuration management
- Database initialization
- Tracking loop
- System tray UI
- Data export

This is the file that runs when you execute: python -m timelawg
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

from timelawg.config import ConfigManager, print_config
from timelawg.database import Database, format_duration
from timelawg.tracker import TrackerLoop
from timelawg.exporter import Exporter
from timelawg.tray import TrayIcon, enable_startup
from timelawg.screenshot import ScreenshotWorker, get_screenshot_directory
from timelawg.action_screenshot import ActionScreenshotWorker, get_action_screenshot_directory


def _parse_duration_to_seconds(duration_str: str) -> float:
    """
    Parse a duration string like '2h 15m' or '45m' or '30s' back to seconds.

    Args:
        duration_str: Duration in format from format_duration()

    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0

    total = 0.0

    # Handle hours
    if 'h' in duration_str:
        parts = duration_str.split('h')
        total += int(parts[0].strip()) * 3600
        duration_str = parts[1] if len(parts) > 1 else ''

    # Handle minutes
    if 'm' in duration_str:
        parts = duration_str.split('m')
        total += int(parts[0].strip()) * 60
        duration_str = parts[1] if len(parts) > 1 else ''

    # Handle seconds
    if 's' in duration_str:
        parts = duration_str.split('s')
        total += int(parts[0].strip())

    return total


# Version info
try:
    from timelawg import __product_version__
except ImportError:
    __product_version__ = "1.0.0"  # Fallback if not yet generated


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
                    initialfile=f"timelawg_export_{datetime.now().strftime('%Y%m%d')}.json"
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
                # Run migration to populate missing end_time values (safe to run multiple times)
                self.database.migrate_missing_end_times()

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
                    columns = [desc[0] for desc in cursor.description]
                    for row in cursor.fetchall():
                        # Handle end_time column which may not exist in older databases
                        end_time = row['end_time'] if 'end_time' in columns else None
                        events.append({
                            'id': row['id'],
                            'timestamp': row['timestamp'],
                            'duration_seconds': row['duration_seconds'],
                            'end_time': end_time,
                            'app': row['app'],
                            'title': row['title'],
                        })

                # Create window
                root = tk.Tk()
                root.title("LawTime - Last 24 Hours")
                root.geometry("800x500")
                root.attributes('-topmost', True)

                # Create menu bar
                menubar = tk.Menu(root)
                root.config(menu=menubar)

                # Help menu with About
                help_menu = tk.Menu(menubar, tearoff=0)
                menubar.add_cascade(label="Help", menu=help_menu)

                def show_about():
                    """Show About dialog with version and commit info."""
                    try:
                        from timelawg import __version__, __product_version__
                    except ImportError:
                        __version__ = "0.0.0.dev"
                        __product_version__ = "0.0.0"

                    # Extract commit ID from version (format: "1.0.0+89e840f")
                    if '+' in __version__:
                        commit_id = __version__.split('+')[1][:7]
                    else:
                        commit_id = "dev"

                    messagebox.showinfo(
                        "About TimeLawg",
                        f"TimeLawg\n\n"
                        f"Version: {__product_version__}\n"
                        f"Build: {commit_id}\n\n"
                        f"Automatic time tracking for lawyers.\n"
                        f"All data stays local for attorney-client privilege.",
                        parent=root
                    )

                help_menu.add_command(label="About", command=show_about)

                # Header frame
                header = tk.Frame(root, pady=10)
                header.pack(fill=tk.X)

                # Calculate totals (only count events with duration recorded)
                total_seconds = sum(
                    e['duration_seconds'] for e in events
                    if e['duration_seconds'] is not None
                )
                header_label = tk.Label(
                    header,
                    text=f"Activity: {format_duration(total_seconds)} ({len(events)} events)",
                    font=('Segoe UI', 12, 'bold')
                )
                header_label.pack()

                # Treeview for events with start time, duration, end time columns
                columns = ('id', 'start', 'duration', 'end', 'app', 'title')
                tree = ttk.Treeview(root, columns=columns, show='headings', selectmode='extended')
                tree.heading('id', text='ID')
                tree.heading('start', text='Start')
                tree.heading('duration', text='Duration')
                tree.heading('end', text='End')
                tree.heading('app', text='Application')
                tree.heading('title', text='Window Title')

                tree.column('id', width=0, stretch=False)  # Hidden column
                tree.column('start', width=140, minwidth=100)
                tree.column('duration', width=70, minwidth=50)
                tree.column('end', width=140, minwidth=100)
                tree.column('app', width=100, minwidth=80)
                tree.column('title', width=330, minwidth=200)

                # Scrollbar
                scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)

                # Function to recalculate and update header totals
                def update_header_totals():
                    """Recalculate and update the header with current totals."""
                    total_secs = 0
                    count = 0
                    for item in tree.get_children():
                        values = tree.item(item, 'values')
                        dur_str = values[2]  # Duration is third column (index 2)
                        if dur_str:
                            # Parse duration string back to seconds
                            total_secs += _parse_duration_to_seconds(dur_str)
                        count += 1
                    header_label.config(
                        text=f"Activity: {format_duration(total_secs)} ({count} events)"
                    )

                # Function to handle command execution
                def execute_command(event=None):
                    """Execute command entered in the text field."""
                    command = command_entry.get().strip().lower()

                    if not command:
                        return

                    try:
                        # Check for quit command first (case insensitive)
                        if command == "quit":
                            # Close the view time window
                            root.destroy()
                            # Quit the application
                            logging.info("Quit command received from command field")
                            # Stop the tray icon first to release the main thread event loop
                            if self.tray and self.tray.icon:
                                self.tray.icon.stop()
                            # Then run cleanup
                            self.quit_app()
                            return

                        # Check for delete command
                        if command == "delete":
                            # Get selected items
                            selected = tree.selection()

                            if not selected:
                                messagebox.showwarning(
                                    "No Selection",
                                    "Please select one or more entries to delete.",
                                    parent=root
                                )
                                command_entry.delete(0, tk.END)
                                return

                            # Get event IDs from selected rows
                            event_ids = []
                            for item in selected:
                                values = tree.item(item, 'values')
                                event_id = int(values[0])  # ID is first column
                                event_ids.append(event_id)

                            # Confirm deletion
                            count = len(event_ids)
                            confirm = messagebox.askyesno(
                                "Confirm Deletion",
                                f"Delete {count} selected {'entry' if count == 1 else 'entries'}?\n\n"
                                f"This action cannot be undone.",
                                parent=root
                            )

                            if not confirm:
                                command_entry.delete(0, tk.END)
                                return

                            # Delete from database
                            deleted = self.database.delete_events_by_ids(event_ids)
                            logging.info(f"Deleted {deleted} events via delete command")

                            # Remove from Treeview
                            for item in selected:
                                tree.delete(item)

                            # Update header totals
                            update_header_totals()

                            # Show success message
                            messagebox.showinfo(
                                "Deleted",
                                f"Successfully deleted {deleted} {'entry' if deleted == 1 else 'entries'}.",
                                parent=root
                            )

                            command_entry.delete(0, tk.END)
                            return

                        # Determine which directory to open based on command
                        if command == "screenshots":
                            # Main screenshots directory
                            target_dir = get_screenshot_directory().parent
                        elif command == "periodic":
                            # Periodic screenshots subdirectory
                            target_dir = get_screenshot_directory()
                        elif command == "actions":
                            # Actions screenshots subdirectory
                            target_dir = get_action_screenshot_directory()
                        else:
                            # Unknown command
                            messagebox.showwarning(
                                "Unknown Command",
                                f"Unknown command: '{command}'\n\n"
                                f"Available commands:\n"
                                f"  • delete - Delete selected entries\n"
                                f"  • screenshots - Open main screenshots folder\n"
                                f"  • periodic - Open periodic screenshots folder\n"
                                f"  • actions - Open action screenshots folder\n"
                                f"  • quit - Close application",
                                parent=root
                            )
                            return

                        # Ensure the directory exists
                        target_dir.mkdir(parents=True, exist_ok=True)

                        # Open in Windows Explorer
                        os.startfile(str(target_dir))
                        logging.info(f"Opened directory: {target_dir}")

                        # Clear the command entry
                        command_entry.delete(0, tk.END)

                    except Exception as e:
                        logging.error(f"Error executing command '{command}': {e}")
                        messagebox.showerror(
                            "Error",
                            f"Could not open directory:\n{str(e)}",
                            parent=root
                        )

                # Button frame - pack BEFORE treeview so it reserves space at top
                btn_frame = tk.Frame(root, pady=5)
                btn_frame.pack(fill=tk.X, side=tk.TOP)

                # Command label
                tk.Label(
                    btn_frame,
                    text="Command:",
                    font=('Segoe UI', 9)
                ).pack(side=tk.LEFT, padx=(10, 5))

                # Command entry field
                command_entry = tk.Entry(
                    btn_frame,
                    width=30,
                    font=('Segoe UI', 9)
                )
                command_entry.pack(side=tk.LEFT, padx=5)
                command_entry.bind('<Return>', execute_command)

                # Help text
                tk.Label(
                    btn_frame,                    
                    font=('Segoe UI', 8),
                    foreground='gray'
                ).pack(side=tk.LEFT, padx=5)

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
                    # Start time - always show (required field)
                    start_ts = event['timestamp'][:19].replace('T', ' ')

                    # Duration - show blank if not recorded (don't calculate)
                    dur = ''
                    if event['duration_seconds'] is not None:
                        dur = format_duration(event['duration_seconds'])

                    # End time - show blank if not recorded (don't calculate)
                    end_ts = ''
                    if event.get('end_time'):
                        end_ts = event['end_time'][:19].replace('T', ' ')

                    app = event['app'] or ''
                    title = event['title'] or ''
                    tree.insert('', tk.END, values=(event['id'], start_ts, dur, end_ts, app, title))

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

        # Ensure "Start with Windows" is enabled on every run
        enable_startup()

        # Show welcome message
        print("\n" + "="*60)
        print(f"TimeLawg v{__product_version__}")
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
