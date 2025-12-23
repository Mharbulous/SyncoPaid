"""
UI windows for SyncoPaid main application.

Contains the Main window implementation.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from syncopaid.database import format_duration
from syncopaid.main_ui_utilities import set_window_icon
from syncopaid.main_ui_commands import create_command_handler
from syncopaid.main_ui_assignment_dialog import show_assignment_dialog
from syncopaid.main_ui_import_dialog import show_import_dialog


def show_main_window(database, tray, quit_callback):
    """
    Show main application window displaying activity from the past 24 hours.

    Args:
        database: Database instance for querying events
        tray: TrayIcon instance for stopping the tray
        quit_callback: Callback function to quit the application
    """
    logging.info("show_main_window called - starting window thread")

    def run_window():
        logging.info("run_window thread started")
        try:
            # Query events from the past 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            cutoff_iso = cutoff.isoformat()

            # Get events directly with timestamp comparison
            events = []
            with database._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT id, timestamp, duration_seconds, end_time, app, title, client, matter
                       FROM events
                       WHERE timestamp >= ? AND is_idle = 0
                       ORDER BY timestamp DESC""",
                    (cutoff_iso,)
                )
                for row in cursor.fetchall():
                    events.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'duration_seconds': row['duration_seconds'],
                        'end_time': row['end_time'],
                        'app': row['app'],
                        'title': row['title'],
                        'client': row['client'],
                        'matter': row['matter'],
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

            def open_import_dialog():
                show_import_dialog(database)

            file_menu.add_command(label="Import Clients && Matters...", command=open_import_dialog)
            file_menu.add_separator()

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
                from syncopaid.screenshot import get_screenshot_directory
                import os
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

            def review_screenshots():
                """Open screenshot review dialog for deletion."""
                from syncopaid.screenshot_review_dialog import show_screenshot_review_dialog
                show_screenshot_review_dialog(root, database)

            view_menu.add_command(label="Review && Delete Screenshots...", command=review_screenshots)

            def view_timeline():
                """Open timeline view window."""
                from syncopaid.timeline_view import show_timeline_window
                show_timeline_window(database)

            view_menu.add_command(label="View Timeline", command=view_timeline)

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
            columns = ('id', 'start', 'duration', 'end', 'app', 'title', 'client', 'matter')
            tree = ttk.Treeview(root, columns=columns, show='headings', selectmode='extended')
            tree.heading('id', text='ID')
            tree.heading('start', text='Start')
            tree.heading('duration', text='Duration')
            tree.heading('end', text='End')
            tree.heading('app', text='Application')
            tree.heading('title', text='Window Title')
            tree.heading('client', text='Client')
            tree.heading('matter', text='Matter')

            tree.column('id', width=0, stretch=False)  # Hidden column
            tree.column('start', width=140, minwidth=100)
            tree.column('duration', width=70, minwidth=50)
            tree.column('end', width=140, minwidth=100)
            tree.column('app', width=100, minwidth=80)
            tree.column('title', width=330, minwidth=200)
            tree.column('client', width=120, minwidth=80)
            tree.column('matter', width=120, minwidth=80)

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

            # Create command handler
            execute_command = create_command_handler(
                tree, database, tray, quit_callback, root, header_label
            )

            # Bind Enter key to execute command
            command_entry.bind('<Return>', lambda e: execute_command(command_entry, e))

            # Bind double-click to open assignment dialog
            def on_double_click(event):
                selection = tree.selection()
                if not selection:
                    return
                item = tree.item(selection[0])
                values = item['values']
                event_id = values[0]
                current_client = values[6] if len(values) > 6 else ''
                current_matter = values[7] if len(values) > 7 else ''

                def on_save(client, matter):
                    # Update treeview
                    tree.set(selection[0], 'client', client or '')
                    tree.set(selection[0], 'matter', matter or '')

                show_assignment_dialog(database, event_id, current_client, current_matter, on_save)

            tree.bind('<Double-1>', on_double_click)

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
                client = event.get('client') or ''
                matter = event.get('matter') or ''
                tree.insert('', tk.END, values=(event['id'], start_ts, dur, end_ts, app, title, client, matter))

            root.mainloop()

        except Exception as e:
            logging.error(f"Error showing main window: {e}", exc_info=True)
            # Show error in a messagebox so it's visible even without console
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"Error opening SyncoPaid window:\n\n{type(e).__name__}: {e}",
                    "SyncoPaid Error",
                    0x10  # MB_ICONERROR
                )
            except Exception:
                pass  # If even the messagebox fails, we can't do much

    # Run in thread to avoid blocking pystray
    window_thread = threading.Thread(target=run_window, daemon=True)
    window_thread.start()
