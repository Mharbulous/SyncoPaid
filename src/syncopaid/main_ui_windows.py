"""
UI windows for SyncoPaid main application.

Contains the Main window implementation.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta

from syncopaid.database import format_duration
from syncopaid.main_ui_utilities import set_window_icon
from syncopaid.main_ui_commands import create_command_handler


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

    # Run in thread to avoid blocking pystray
    window_thread = threading.Thread(target=run_window, daemon=True)
    window_thread.start()


def show_import_dialog(database):
    """Show dialog for importing client/matter data from folder structure."""

    def run_dialog():
        from syncopaid.client_matter_importer import import_from_folder

        root = tk.Tk()
        root.title("Import Clients & Matters")
        root.geometry("600x400")
        root.attributes('-topmost', True)
        set_window_icon(root)

        # State
        import_result = None

        # Folder selection frame
        folder_frame = tk.Frame(root, pady=10, padx=10)
        folder_frame.pack(fill=tk.X)

        tk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        folder_var = tk.StringVar()
        folder_entry = tk.Entry(folder_frame, textvariable=folder_var, width=40)
        folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def browse_folder():
            nonlocal import_result
            path = filedialog.askdirectory(parent=root, title="Select Client Folder")
            if path:
                folder_var.set(path)
                import_result = import_from_folder(path)
                update_preview()

        tk.Button(folder_frame, text="Browse...", command=browse_folder).pack(side=tk.LEFT)

        # Preview label
        preview_label = tk.Label(root, text="Select a folder to preview", pady=5)
        preview_label.pack()

        # Preview frame with treeview
        preview_frame = tk.Frame(root)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        columns = ('client', 'matter')
        tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=10)
        tree.heading('client', text='Client')
        tree.heading('matter', text='Matter')
        tree.column('client', width=200)
        tree.column('matter', width=300)

        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def update_preview():
            for item in tree.get_children():
                tree.delete(item)

            if import_result:
                preview_label.config(
                    text=f"Found {import_result.stats['clients']} clients, "
                         f"{import_result.stats['matters']} matters"
                )
                for m in import_result.matters:
                    tree.insert('', tk.END, values=(
                        m.client_display_name,
                        m.display_name
                    ))

        # Button frame
        btn_frame = tk.Frame(root, pady=10, padx=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def do_import():
            if not import_result or not import_result.clients:
                messagebox.showwarning("No Data",
                    "No clients found in selected folder.", parent=root)
                return

            try:
                save_import_to_database(database, import_result)
                messagebox.showinfo("Import Complete",
                    f"Imported {import_result.stats['clients']} clients and "
                    f"{import_result.stats['matters']} matters.", parent=root)
                root.destroy()
            except Exception as e:
                logging.error(f"Import failed: {e}", exc_info=True)
                messagebox.showerror("Import Failed", str(e), parent=root)

        tk.Button(btn_frame, text="Cancel", command=root.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Import", command=do_import, width=10).pack(side=tk.RIGHT, padx=5)

        root.mainloop()

    dialog_thread = threading.Thread(target=run_dialog, daemon=True)
    dialog_thread.start()


def save_import_to_database(database, import_result):
    """Save imported clients and matters to database."""
    with database._get_connection() as conn:
        cursor = conn.cursor()

        # Build client ID map
        client_ids = {}
        for client in import_result.clients:
            cursor.execute("""
                INSERT OR IGNORE INTO clients (display_name, folder_path)
                VALUES (?, ?)
            """, (client.display_name, client.folder_path))

            cursor.execute(
                "SELECT id FROM clients WHERE display_name = ?",
                (client.display_name,)
            )
            row = cursor.fetchone()
            if row:
                client_ids[client.display_name] = row[0]

        # Insert matters
        for matter in import_result.matters:
            client_id = client_ids.get(matter.client_display_name)
            if client_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO matters
                    (client_id, display_name, folder_path)
                    VALUES (?, ?, ?)
                """, (client_id, matter.display_name, matter.folder_path))

        conn.commit()
