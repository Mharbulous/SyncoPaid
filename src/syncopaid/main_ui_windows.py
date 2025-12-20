"""
UI windows for SyncoPaid main application.

Contains the Main window and Export dialog implementations.
"""

import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date, timedelta
from pathlib import Path

from syncopaid.database import format_duration
from syncopaid.screenshot import get_screenshot_directory
from syncopaid.action_screenshot import get_action_screenshot_directory
from syncopaid.tray import get_resource_path


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


def set_window_icon(root: tk.Tk) -> None:
    """Set the SyncoPaid icon on a tkinter window (Main window)."""
    try:
        if sys.platform == 'win32':
            icon_path = get_resource_path("assets/SYNCOPaiD.ico")
            logging.debug(f"Window icon path: {icon_path}")
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
                logging.debug("Window icon set successfully")
            else:
                logging.warning(f"Window icon not found: {icon_path}")
    except Exception as e:
        logging.warning(f"Could not set window icon: {e}")


def show_export_dialog(exporter, database):
    """
    Show dialog for exporting data.

    Args:
        exporter: Exporter instance for performing the export
        database: Database instance for accessing data
    """
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
                initialfile=f"SyncoPaid_export_{datetime.now().strftime('%Y%m%d')}.json"
            )

            if output_path:
                # Get date range (default: today)
                today = date.today().isoformat()

                # Simple dialog for date range (can be enhanced later)
                # For MVP, just export today's data
                result = exporter.export_to_json(
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


def show_main_window(database, tray, quit_callback):
    """
    Show main application window displaying activity from the past 24 hours.

    Args:
        database: Database instance for querying events
        tray: TrayIcon instance for stopping the tray
        quit_callback: Callback function to quit the application
    """
    def run_window():
        try:
            # Query events from the past 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            cutoff_iso = cutoff.isoformat()

            # Get events directly with timestamp comparison
            events = []
            with database._get_connection() as conn:
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
            root.title("SyncoPaid - Last 24 Hours")
            root.geometry("800x500")
            root.attributes('-topmost', True)
            set_window_icon(root)

            # Create menu bar
            menubar = tk.Menu(root)
            root.config(menu=menubar)

            # File menu with Exit
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)

            def exit_program():
                """Exit the application."""
                root.destroy()
                logging.info("Exit command received from File menu")
                if tray and tray.icon:
                    tray.icon.stop()
                quit_callback()

            file_menu.add_command(label="Exit", command=exit_program)

            # View menu with View Screenshots
            view_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="View", menu=view_menu)

            def view_screenshots():
                """Open screenshots folder in File Explorer."""
                screenshots_dir = get_screenshot_directory().parent
                if screenshots_dir.exists():
                    os.startfile(str(screenshots_dir))
                else:
                    messagebox.showwarning(
                        "Screenshots",
                        f"Screenshots folder not found:\n{screenshots_dir}",
                        parent=root
                    )

            view_menu.add_command(label="View Screenshots", command=view_screenshots)

            # Help menu with About
            help_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Help", menu=help_menu)

            def show_about():
                """Show About dialog with version and commit info."""
                try:
                    from syncopaid import __version__, __product_version__
                except ImportError:
                    __version__ = "0.0.0.dev"
                    __product_version__ = "0.0.0"

                # Extract commit ID from version (format: "1.0.0+89e840f")
                if '+' in __version__:
                    commit_id = __version__.split('+')[1][:7]
                else:
                    commit_id = "dev"

                messagebox.showinfo(
                    "About SyncoPaid",
                    f"SyncoPaid\n\n"
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

            # Command entry frame (at bottom)
            command_frame = tk.Frame(root, pady=10)
            command_frame.pack(fill=tk.X, side=tk.BOTTOM)

            tk.Label(
                command_frame,
                text="Command:",
                font=('Segoe UI', 10)
            ).pack(side=tk.LEFT, padx=(10, 5))

            command_entry = tk.Entry(command_frame, font=('Segoe UI', 10))
            command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

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

            def execute_command(event=None):
                """Execute command entered by user."""
                command = command_entry.get().strip().lower()

                if not command:
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
                    deleted = database.delete_events_by_ids(event_ids)
                    logging.info(f"Deleted {deleted} events via delete command")

                    # Remove from Treeview
                    for item in selected:
                        tree.delete(item)

                    # Update header totals
                    update_header_totals()

                    messagebox.showinfo(
                        "Deleted",
                        f"Successfully deleted {deleted} {'entry' if deleted == 1 else 'entries'}.",
                        parent=root
                    )

                    command_entry.delete(0, tk.END)
                    return

                # Check for screenshots command
                elif command == "screenshots":
                    screenshots_dir = get_screenshot_directory().parent
                    if screenshots_dir.exists():
                        os.startfile(str(screenshots_dir))
                    else:
                        messagebox.showwarning(
                            "Screenshots",
                            f"Screenshots folder not found:\n{screenshots_dir}",
                            parent=root
                        )
                    command_entry.delete(0, tk.END)
                    return

                # Check for periodic command
                elif command == "periodic":
                    periodic_dir = get_screenshot_directory()
                    if periodic_dir.exists():
                        os.startfile(str(periodic_dir))
                    else:
                        messagebox.showwarning(
                            "Periodic Screenshots",
                            f"Periodic screenshots folder not found:\n{periodic_dir}",
                            parent=root
                        )
                    command_entry.delete(0, tk.END)
                    return

                # Check for actions command
                elif command == "actions":
                    actions_dir = get_action_screenshot_directory()
                    if actions_dir.exists():
                        os.startfile(str(actions_dir))
                    else:
                        messagebox.showwarning(
                            "Action Screenshots",
                            f"Action screenshots folder not found:\n{actions_dir}",
                            parent=root
                        )
                    command_entry.delete(0, tk.END)
                    return

                # Check for quit command
                elif command == "quit":
                    root.destroy()
                    if tray and tray.icon:
                        tray.icon.stop()
                    quit_callback()
                    return

                # Unknown command
                else:
                    messagebox.showwarning(
                        "Unknown Command",
                        f"Unknown command: '{command}'\n\n"
                        f"Available commands:\n"
                        f"  - delete - Delete selected entries\n"
                        f"  - screenshots - Open main screenshots folder\n"
                        f"  - periodic - Open periodic screenshots folder\n"
                        f"  - actions - Open action screenshots folder\n"
                        f"  - quit - Close application",
                        parent=root
                    )
                    command_entry.delete(0, tk.END)

            # Bind Enter key to execute command
            command_entry.bind('<Return>', execute_command)

            # Button frame
            btn_frame = tk.Frame(root, pady=5)
            btn_frame.pack(fill=tk.X, side=tk.TOP)

            tk.Button(
                btn_frame,
                text="Close",
                command=root.destroy,
                width=10
            ).pack(side=tk.RIGHT, padx=10)

            # Pack treeview and scrollbar
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
            logging.error(f"Error showing main window: {e}", exc_info=True)

    # Run in thread to avoid blocking pystray
    window_thread = threading.Thread(target=run_window, daemon=True)
    window_thread.start()
