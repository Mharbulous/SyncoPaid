"""
Command handling for SyncoPaid main window.

Contains command execution logic for the main window command entry.
"""

import os
import logging
import tkinter as tk
from tkinter import messagebox

from syncopaid.screenshot import get_screenshot_directory
from syncopaid.action_screenshot import get_action_screenshot_directory
from syncopaid.main_ui_utilities import parse_duration_to_seconds
from syncopaid.database import format_duration


def create_command_handler(tree, database, tray, quit_callback, root, header_label):
    """
    Create command execution handler for the main window.

    Args:
        tree: Treeview widget displaying events
        database: Database instance for operations
        tray: TrayIcon instance for stopping the tray
        quit_callback: Callback function to quit the application
        root: Root Tk window
        header_label: Label widget for header totals

    Returns:
        Callable that executes commands
    """
    def update_header_totals():
        """Recalculate and update the header with current totals."""
        total_secs = 0
        count = 0
        for item in tree.get_children():
            values = tree.item(item, 'values')
            dur_str = values[2]  # Duration is third column (index 2)
            if dur_str:
                # Parse duration string back to seconds
                total_secs += parse_duration_to_seconds(dur_str)
            count += 1
        header_label.config(
            text=f"Activity: {format_duration(total_secs)} ({count} events)"
        )

    def execute_command(command_entry, event=None):
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

    return execute_command
