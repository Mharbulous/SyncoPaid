"""Matter edit/add dialog."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from syncopaid.database import Database


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
