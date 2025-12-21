"""Client management dialogs."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from syncopaid.database import Database


class ClientDialog:
    """Dialog for managing clients."""

    def __init__(self, parent, db: Database, on_close: Optional[Callable] = None):
        self.db = db
        self.on_close = on_close

        self.window = tk.Toplevel(parent)
        self.window.title("Manage Clients")
        self.window.geometry("600x400")

        # Client list
        list_frame = ttk.Frame(self.window, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(list_frame, text="Clients:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        self.client_listbox = tk.Listbox(list_frame, height=15)
        self.client_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Add Client", command=self._add_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Client", command=self._edit_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Client", command=self._delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self._close).pack(side=tk.RIGHT, padx=5)

        self._refresh_list()
        self.window.transient(parent)
        self.window.grab_set()

    def _refresh_list(self):
        self.client_listbox.delete(0, tk.END)
        self.clients = self.db.get_clients()
        for client in self.clients:
            display = f"{client['name']}"
            if client['notes']:
                display += f" - {client['notes'][:50]}"
            self.client_listbox.insert(tk.END, display)

    def _add_client(self):
        dialog = ClientEditDialog(self.window, self.db)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _edit_client(self):
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to edit.")
            return
        client = self.clients[selection[0]]
        dialog = ClientEditDialog(self.window, self.db, client)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _delete_client(self):
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to delete.")
            return
        client = self.clients[selection[0]]
        if messagebox.askyesno("Confirm Delete", f"Delete client '{client['name']}'?"):
            self.db.delete_client(client['id'])
            self._refresh_list()

    def _close(self):
        if self.on_close:
            self.on_close()
        self.window.destroy()


class ClientEditDialog:
    """Dialog for adding/editing a single client."""

    def __init__(self, parent, db: Database, client: Optional[dict] = None):
        self.db = db
        self.client = client

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Client" if client else "Add Client")
        self.window.geometry("400x200")

        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Client Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=client['name'] if client else "")
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)

        ttk.Label(form_frame, text="Notes:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.notes_var = tk.StringVar(value=client['notes'] if client and client['notes'] else "")
        ttk.Entry(form_frame, textvariable=self.notes_var, width=40).grid(row=1, column=1, pady=5)

        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        self.window.transient(parent)
        self.window.grab_set()

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Validation Error", "Client name is required.")
            return

        notes = self.notes_var.get().strip() or None

        if self.client:
            self.db.update_client(self.client['id'], name, notes)
        else:
            self.db.insert_client(name, notes)

        self.window.destroy()
