"""
Export dialog for SyncoPaid main application.

Contains the export dialog implementation.
"""

import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime, date


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
