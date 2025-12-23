"""
Import dialog for client/matter data.

Provides UI for importing client and matter data from folder structures.
Includes instructional panel showing expected folder structure.
"""

import logging
import threading
import tkinter as tk
from tkinter import messagebox

from syncopaid.main_ui_utilities import set_window_icon
from syncopaid.main_ui_import_dialog_ui import (
    create_instructional_panel,
    create_folder_selection,
    create_preview_section
)
from syncopaid.main_ui_import_dialog_db import save_import_to_database


def show_import_dialog(database):
    """Show dialog for importing client/matter data from folder structure."""

    def run_dialog():
        from syncopaid.client_matter_importer import import_from_folder

        root = tk.Tk()
        root.title("Import Clients & Matters")
        root.geometry("650x520")
        root.attributes('-topmost', True)
        set_window_icon(root)

        # State
        import_result = None

        # Preview widgets - declare first so callback can reference them
        tree = None
        preview_label = None
        status_label = None
        update_preview = None

        def on_folder_selected(path):
            nonlocal import_result
            # Show scanning state
            preview_label.config(text="Scanning...")
            status_label.config(text="", fg='#666666')
            root.update()
            # Perform scan
            import_result = import_from_folder(path)
            update_preview(import_result)

        # Build UI sections in correct order
        create_instructional_panel(root)
        folder_var = create_folder_selection(root, on_folder_selected)
        tree, preview_label, status_label, update_preview = create_preview_section(root)

        # Button frame
        btn_frame = tk.Frame(root, pady=12, padx=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def do_import():
            if not import_result or not import_result.clients:
                messagebox.showwarning(
                    "No Data",
                    "No clients found in selected folder.\n\n"
                    "Make sure you selected a folder that contains "
                    "client subfolders.",
                    parent=root
                )
                return

            try:
                save_import_to_database(database, import_result)
                messagebox.showinfo(
                    "Import Complete",
                    f"Imported {import_result.stats['clients']} clients and "
                    f"{import_result.stats['matters']} matters.",
                    parent=root
                )
                root.destroy()
            except Exception as e:
                logging.error(f"Import failed: {e}", exc_info=True)
                messagebox.showerror("Import Failed", str(e), parent=root)

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=root.destroy,
            width=10,
            font=('Segoe UI', 9)
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        import_btn = tk.Button(
            btn_frame,
            text="Import",
            command=do_import,
            width=10,
            font=('Segoe UI', 9)
        )
        import_btn.pack(side=tk.RIGHT, padx=5)

        root.mainloop()

    dialog_thread = threading.Thread(target=run_dialog, daemon=True)
    dialog_thread.start()
