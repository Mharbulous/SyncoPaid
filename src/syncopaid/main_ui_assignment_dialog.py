"""
Assignment dialog for assigning client/matter to events.

Provides UI for selecting and updating client/matter assignments on activity events.
"""

import tkinter as tk
from tkinter import ttk


def show_assignment_dialog(database, event_id, current_client, current_matter, on_save):
    """Show dialog to assign client/matter to an event."""
    root = tk.Toplevel()
    root.title("Assign Client/Matter")
    root.geometry("350x150")
    root.attributes('-topmost', True)
    root.grab_set()  # Modal

    # Fetch available clients
    clients = []
    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT display_name FROM clients ORDER BY display_name")
        clients = [row[0] for row in cursor.fetchall()]

    # Client selection
    tk.Label(root, text="Client:", pady=5).grid(row=0, column=0, sticky='e', padx=10)
    client_var = tk.StringVar(value=current_client or '')
    client_combo = ttk.Combobox(root, textvariable=client_var, values=clients, width=30)
    client_combo.grid(row=0, column=1, pady=5, padx=10)

    # Matter selection (filtered by client)
    tk.Label(root, text="Matter:", pady=5).grid(row=1, column=0, sticky='e', padx=10)
    matter_var = tk.StringVar(value=current_matter or '')
    matter_combo = ttk.Combobox(root, textvariable=matter_var, width=30)
    matter_combo.grid(row=1, column=1, pady=5, padx=10)

    def update_matters(*args):
        """Update matter dropdown when client changes."""
        selected_client = client_var.get()
        matters = []
        if selected_client:
            with database._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.display_name FROM matters m
                    JOIN clients c ON m.client_id = c.id
                    WHERE c.display_name = ?
                    ORDER BY m.display_name
                """, (selected_client,))
                matters = [row[0] for row in cursor.fetchall()]
        matter_combo['values'] = matters
        if matter_var.get() not in matters:
            matter_var.set('')

    client_var.trace_add('write', update_matters)
    update_matters()  # Initial population

    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=15)

    def save():
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events SET client = ?, matter = ? WHERE id = ?
            """, (client_var.get() or None, matter_var.get() or None, event_id))
            conn.commit()
        on_save(client_var.get(), matter_var.get())
        root.destroy()

    tk.Button(btn_frame, text="Cancel", command=root.destroy, width=8).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Save", command=save, width=8).pack(side=tk.LEFT, padx=5)
