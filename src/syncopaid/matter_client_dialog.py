"""Client and matter management dialogs."""
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable
from syncopaid.database import Database


def export_matters_csv(db: Database, csv_path: str):
    """Export all matters to CSV file."""
    matters = db.get_matters(status='all')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['matter_number', 'client_name', 'description', 'status'])
        writer.writeheader()
        for matter in matters:
            writer.writerow({
                'matter_number': matter['matter_number'],
                'client_name': matter.get('client_name', ''),
                'description': matter.get('description', ''),
                'status': matter['status']
            })

def import_matters_csv(db: Database, csv_path: str):
    """Import matters from CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Find or create client
            client_id = None
            client_name = row.get('client_name', '').strip()
            if client_name:
                for c in db.get_clients():
                    if c['name'] == client_name:
                        client_id = c['id']
                        break
                if client_id is None:
                    client_id = db.insert_client(name=client_name)

            try:
                db.insert_matter(
                    matter_number=row['matter_number'],
                    client_id=client_id,
                    description=row.get('description', '').strip() or None,
                    status=row.get('status', 'active')
                )
            except Exception:
                pass  # Skip duplicates


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
        self.matter_listbox = tk.Listbox(list_frame, height=15)
        self.matter_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

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
        self.matter_listbox.delete(0, tk.END)
        self.matters = self.db.get_matters(status=self.status_filter.get())
        for matter in self.matters:
            display = f"[{matter['matter_number']}] {matter.get('client_name', 'No Client')}"
            if matter['status'] == 'archived':
                display += " (ARCHIVED)"
            self.matter_listbox.insert(tk.END, display)

    def _add_matter(self):
        dialog = MatterEditDialog(self.window, self.db)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _edit_matter(self):
        selection = self.matter_listbox.curselection()
        if not selection:
            return messagebox.showwarning("No Selection", "Please select a matter.")
        dialog = MatterEditDialog(self.window, self.db, self.matters[selection[0]])
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _toggle_status(self):
        selection = self.matter_listbox.curselection()
        if not selection:
            return messagebox.showwarning("No Selection", "Please select a matter.")
        matter = self.matters[selection[0]]
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
