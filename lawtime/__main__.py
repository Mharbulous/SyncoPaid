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
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime, date

from .config import ConfigManager, print_config
from .database import Database, format_duration
from .tracker import TrackerLoop
from .exporter import Exporter
from .tray import TrayIcon


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
        
        # Initialize tracker loop
        self.tracker = TrackerLoop(
            poll_interval=self.config.poll_interval_seconds,
            idle_threshold=self.config.idle_threshold_seconds,
            merge_threshold=self.config.merge_threshold_seconds
        )
        
        # Tracking state
        self.tracking_thread: threading.Thread = None
        self.is_tracking = False
        
        # System tray
        self.tray = TrayIcon(
            on_start=self.start_tracking,
            on_pause=self.pause_tracking,
            on_export=self.show_export_dialog,
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
        
        logging.info("Tracking started")
        print("✓ Tracking started")
    
    def pause_tracking(self):
        """Pause the tracking loop."""
        if not self.is_tracking:
            logging.warning("Tracking not running")
            return
        
        self.is_tracking = False
        self.tracker.stop()
        
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
        
        # Show final statistics
        self.show_statistics()
        
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
    
    try:
        app = LawTimeApp()
        app.run()
    
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
