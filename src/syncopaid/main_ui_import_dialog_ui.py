"""
UI construction for import dialog.

Builds the instructional panel, folder selection, and preview sections.
"""

import tkinter as tk
from tkinter import ttk, filedialog


# ASCII folder tree diagram for instructional panel
FOLDER_STRUCTURE_DIAGRAM = """📁 Your Root Folder  ← Select this folder
    📁 0001 - Acme Corp
        📁 001 - Annual Review
        📁 002 - Contract Dispute
    📁 0002 - Smith & Associates
        📁 001 - Estate Planning
        📁 002 - Merger Acquisition"""


def create_instructional_panel(root):
    """Create and return the instructional panel showing expected folder structure."""
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


def create_folder_selection(root, on_folder_selected):
    """
    Create and return folder selection UI.

    Args:
        root: Parent window
        on_folder_selected: Callback function(path) when folder is selected

    Returns:
        folder_var: StringVar holding the selected folder path
    """
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
        path = filedialog.askdirectory(
            parent=root,
            title="Select Root Folder Containing Client Folders"
        )
        if path:
            folder_var.set(path)
            on_folder_selected(path)

    browse_btn = tk.Button(
        folder_frame,
        text="Browse...",
        command=browse_folder,
        font=('Segoe UI', 9)
    )
    browse_btn.pack(side=tk.LEFT)

    return folder_var


def create_preview_section(root):
    """
    Create and return preview section with treeview.

    Returns:
        tuple: (tree, preview_label, status_label, update_preview_func)
    """
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

    def update_preview(import_result):
        """Update preview tree with import results."""
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

    return tree, preview_label, status_label, update_preview
