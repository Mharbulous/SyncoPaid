"""Matter management dialogs."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable
from syncopaid.database import Database
from syncopaid.matter_client_csv import import_matters_csv, export_matters_csv


def format_keywords_for_display(
    keywords: list,
    max_display: int = 5
) -> str:
    """
    Format keywords list for UI display.

    Args:
        keywords: List of keyword dicts with 'keyword' and 'confidence'
        max_display: Maximum keywords to show before truncating

    Returns:
        Comma-separated string of keywords, with "..." if truncated
    """
    if not keywords:
        return ""

    # Sort by confidence (should already be sorted, but ensure)
    sorted_kw = sorted(keywords, key=lambda k: k.get('confidence', 0), reverse=True)

    # Take top N keywords
    display_kw = [k['keyword'] for k in sorted_kw[:max_display]]

    # Add ellipsis if truncated
    if len(sorted_kw) > max_display:
        display_kw.append("...")

    return ", ".join(display_kw)


def get_matters_with_keywords(db) -> list:
    """
    Get all matters with their AI-extracted keywords formatted for display.

    Args:
        db: Database instance

    Returns:
        List of matter dicts with added 'keywords_display' field
    """
    matters = db.get_matters(status='all')

    for matter in matters:
        keywords = db.get_matter_keywords(matter['id'])
        matter['keywords_display'] = format_keywords_for_display(keywords)
        matter['keywords_raw'] = keywords  # For tooltip/detail view

    return matters


class MatterDialog:
    """Dialog for managing matters."""

    def __init__(self, parent, db: Database, on_close: Optional[Callable] = None):
        self.db = db
        self.on_close = on_close
        self.status_filter = tk.StringVar(value='active')

        self.window = tk.Toplevel(parent)
        self.window.title("Manage Matters")
        self.window.geometry("800x500")

        # Status filter
        control_frame = ttk.Frame(self.window, padding=10)
        control_frame.pack(fill=tk.X)
        ttk.Label(control_frame, text="Show:").pack(side=tk.LEFT, padx=5)
        for status in ['active', 'archived', 'all']:
            ttk.Radiobutton(control_frame, text=status.capitalize(),
                           variable=self.status_filter, value=status,
                           command=self._refresh_list).pack(side=tk.LEFT)

        # Matter list
        list_frame = ttk.Frame(self.window, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview with columns
        columns = ("matter_number", "client", "description", "keywords", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        # Configure column headings
        self.tree.heading("matter_number", text="Matter Number")
        self.tree.heading("client", text="Client")
        self.tree.heading("description", text="Description")
        self.tree.heading("keywords", text="Keywords (AI)")
        self.tree.heading("status", text="Status")

        # Configure column widths
        self.tree.column("matter_number", width=120, minwidth=80)
        self.tree.column("client", width=150, minwidth=100)
        self.tree.column("description", width=200, minwidth=150)
        self.tree.column("keywords", width=200, minwidth=100)
        self.tree.column("status", width=80, minwidth=60)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="Add Matter", command=self._add_matter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Matter", command=self._edit_matter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Toggle Status", command=self._toggle_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import CSV", command=self._import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export CSV", command=self._export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self._close).pack(side=tk.RIGHT, padx=5)

        self._refresh_list()
        self.window.transient(parent)
        self.window.grab_set()

    def _refresh_list(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get matters with keywords
        self.matters = get_matters_with_keywords(self.db)

        # Filter by status
        status_filter = self.status_filter.get()
        if status_filter != 'all':
            self.matters = [m for m in self.matters if m['status'] == status_filter]

        # Populate treeview
        for matter in self.matters:
            client_name = matter.get('client_name', 'No Client')
            description = matter.get('description', '')
            keywords_display = matter.get('keywords_display', '')
            status = matter['status']

            values = (
                matter['matter_number'],
                client_name,
                description,
                keywords_display,
                status
            )
            self.tree.insert('', tk.END, values=values)

    def _add_matter(self):
        dialog = MatterEditDialog(self.window, self.db)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _edit_matter(self):
        selection = self.tree.selection()
        if not selection:
            return messagebox.showwarning("No Selection", "Please select a matter.")
        # Get the index of the selected item
        item_id = selection[0]
        item_index = self.tree.index(item_id)
        dialog = MatterEditDialog(self.window, self.db, self.matters[item_index])
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _toggle_status(self):
        selection = self.tree.selection()
        if not selection:
            return messagebox.showwarning("No Selection", "Please select a matter.")
        # Get the index of the selected item
        item_id = selection[0]
        item_index = self.tree.index(item_id)
        matter = self.matters[item_index]
        new_status = 'archived' if matter['status'] == 'active' else 'active'
        self.db.update_matter_status(matter['id'], new_status)
        self._refresh_list()

    def _import_csv(self):
        path = filedialog.askopenfilename(parent=self.window, filetypes=[("CSV", "*.csv")])
        if path:
            import_matters_csv(self.db, path)
            self._refresh_list()
            messagebox.showinfo("Success", "Matters imported.")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(parent=self.window, defaultextension=".csv")
        if path:
            export_matters_csv(self.db, path)
            messagebox.showinfo("Success", "Matters exported.")

    def _close(self):
        if self.on_close:
            self.on_close()
        self.window.destroy()


class MatterEditDialog:
    """Dialog for adding/editing a single matter."""

    def __init__(self, parent, db: Database, matter: Optional[dict] = None):
        self.db = db
        self.matter = matter

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Matter" if matter else "Add Matter")
        self.window.geometry("500x300")

        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Matter number
        ttk.Label(form_frame, text="Matter Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.matter_number_var = tk.StringVar(value=matter['matter_number'] if matter else "")
        ttk.Entry(form_frame, textvariable=self.matter_number_var, width=40).grid(row=0, column=1, pady=5)

        # Client dropdown
        ttk.Label(form_frame, text="Client:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.clients = db.get_clients()
        client_names = ["(No Client)"] + [c['name'] for c in self.clients]
        self.client_var = tk.StringVar(value="(No Client)")
        if matter and matter.get('client_id'):
            for c in self.clients:
                if c['id'] == matter['client_id']:
                    self.client_var.set(c['name'])
        ttk.Combobox(form_frame, textvariable=self.client_var, values=client_names,
                    state='readonly', width=38).grid(row=1, column=1, pady=5)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar(value=matter['description'] if matter and matter['description'] else "")
        ttk.Entry(form_frame, textvariable=self.description_var, width=40).grid(row=2, column=1, pady=5)

        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        self.window.transient(parent)
        self.window.grab_set()

    def _save(self):
        matter_number = self.matter_number_var.get().strip()
        if not matter_number:
            return messagebox.showerror("Error", "Matter number is required.")

        client_id = None
        client_name = self.client_var.get()
        if client_name != "(No Client)":
            for c in self.clients:
                if c['name'] == client_name:
                    client_id = c['id']
                    break

        description = self.description_var.get().strip() or None

        try:
            if self.matter:
                self.db.update_matter(self.matter['id'], matter_number, client_id, description)
            else:
                self.db.insert_matter(matter_number, client_id, description)
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
