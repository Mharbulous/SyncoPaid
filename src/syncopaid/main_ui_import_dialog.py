"""
Import dialog for client/matter data.

Provides UI for importing client and matter data from folder structures.
Includes instructional panel showing expected folder structure.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from syncopaid.main_ui_utilities import set_window_icon


# ASCII folder tree diagram for instructional panel
FOLDER_STRUCTURE_DIAGRAM = """📁 Your Root Folder  ← Select this folder
    📁 0001 - Acme Corp
        📁 001 - Annual Review
        📁 002 - Contract Dispute
    📁 0002 - Smith & Associates
        📁 001 - Estate Planning
        📁 002 - Merger Acquisition"""


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

        # ══════════════════════════════════════════════════════════════
        # INSTRUCTIONAL PANEL - Expected Folder Structure
        # ══════════════════════════════════════════════════════════════
        instruction_frame = tk.Frame(root, padx=15, pady=10)
        instruction_frame.pack(fill=tk.X)

        # Heading
        heading_label = tk.Label(
            instruction_frame,
            text="Expected Folder Structure",
            font=('Segoe UI', 11, 'bold'),
            anchor='w'
        )
        heading_label.pack(fill=tk.X)

        # Helper text
        helper_text = tk.Label(
            instruction_frame,
            text="Select your root client folder. SyncoPaid will scan for subfolders "
                 "organized by client number and matter number.",
            font=('Segoe UI', 9),
            fg='#555555',
            anchor='w',
            wraplength=600,
            justify='left'
        )
        helper_text.pack(fill=tk.X, pady=(2, 8))

        # Folder tree diagram in a bordered frame
        diagram_frame = tk.Frame(
            instruction_frame,
            bg='#F5F5F5',
            relief='solid',
            borderwidth=1
        )
        diagram_frame.pack(fill=tk.X, pady=(0, 5))

        diagram_label = tk.Label(
            diagram_frame,
            text=FOLDER_STRUCTURE_DIAGRAM,
            font=('Consolas', 9),
            bg='#F5F5F5',
            anchor='w',
            justify='left',
            padx=10,
            pady=8
        )
        diagram_label.pack(fill=tk.X)

        # Format hint
        format_hint = tk.Label(
            instruction_frame,
            text="Format: Client folders at level 1, Matter folders at level 2",
            font=('Segoe UI', 8),
            fg='#777777',
            anchor='w'
        )
        format_hint.pack(fill=tk.X)

        # Separator
        separator = ttk.Separator(root, orient='horizontal')
        separator.pack(fill=tk.X, padx=15, pady=8)

        # ══════════════════════════════════════════════════════════════
        # FOLDER SELECTION
        # ══════════════════════════════════════════════════════════════
        folder_frame = tk.Frame(root, padx=15, pady=5)
        folder_frame.pack(fill=tk.X)

        tk.Label(
            folder_frame,
            text="Root Folder:",
            font=('Segoe UI', 9)
        ).pack(side=tk.LEFT)

        folder_var = tk.StringVar()
        folder_entry = tk.Entry(
            folder_frame,
            textvariable=folder_var,
            width=45,
            font=('Segoe UI', 9)
        )
        folder_entry.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

        def browse_folder():
            nonlocal import_result
            path = filedialog.askdirectory(
                parent=root,
                title="Select Root Folder Containing Client Folders"
            )
            if path:
                folder_var.set(path)
                # Show scanning state
                preview_label.config(text="Scanning...")
                status_label.config(text="", fg='#666666')
                root.update()
                # Perform scan
                import_result = import_from_folder(path)
                update_preview()

        browse_btn = tk.Button(
            folder_frame,
            text="Browse...",
            command=browse_folder,
            font=('Segoe UI', 9)
        )
        browse_btn.pack(side=tk.LEFT)

        # ══════════════════════════════════════════════════════════════
        # PREVIEW SECTION
        # ══════════════════════════════════════════════════════════════
        preview_header = tk.Frame(root, padx=15, pady=(10, 5))
        preview_header.pack(fill=tk.X)

        preview_label = tk.Label(
            preview_header,
            text="Results",
            font=('Segoe UI', 10, 'bold'),
            anchor='w'
        )
        preview_label.pack(side=tk.LEFT)

        status_label = tk.Label(
            preview_header,
            text="No folder selected",
            font=('Segoe UI', 9),
            fg='#666666',
            anchor='e'
        )
        status_label.pack(side=tk.RIGHT)

        # Preview frame with treeview
        preview_frame = tk.Frame(root, padx=15)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('client', 'matter')
        tree = ttk.Treeview(
            preview_frame,
            columns=columns,
            show='headings',
            height=8
        )
        tree.heading('client', text='Client')
        tree.heading('matter', text='Matter')
        tree.column('client', width=220)
        tree.column('matter', width=350)

        scrollbar = ttk.Scrollbar(
            preview_frame,
            orient=tk.VERTICAL,
            command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def update_preview():
            for item in tree.get_children():
                tree.delete(item)

            if import_result:
                client_count = import_result.stats['clients']
                matter_count = import_result.stats['matters']
                # Update header to show finished state
                preview_label.config(text="Finished!")
                status_label.config(
                    text=f"Found {client_count} client{'s' if client_count != 1 else ''}, "
                         f"{matter_count} matter{'s' if matter_count != 1 else ''}",
                    fg='#228B22' if client_count > 0 else '#666666'
                )
                for m in import_result.matters:
                    tree.insert('', tk.END, values=(
                        m.client_display_name,
                        m.display_name
                    ))
            else:
                preview_label.config(text="Results")
                status_label.config(text="No folder selected", fg='#666666')

        # ══════════════════════════════════════════════════════════════
        # BUTTON FRAME
        # ══════════════════════════════════════════════════════════════
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
