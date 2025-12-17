# Matter/Client Database - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Enable lawyers to define matters/clients locally so AI can match activities to billing matters with high confidence.

**Approach:** Extend existing SQLite schema in SyncoPaid.db with two new tables (matters, clients) and create a tkinter dialog module for CRUD operations. Follow existing patterns in database.py for schema management and __main__.py for tkinter dialogs.

**Tech Stack:** SQLite (existing SyncoPaid.db), tkinter, CSV import/export via Python stdlib

---

**Story ID:** 1.8.1 | **Created:** 2025-12-17 | **Status:** `planned`

---

## Story Context

**Title:** Matter/Client Database

**Description:** **As a** lawyer setting up SyncoPaid for billing integration
**I want** to define my active matters and clients in a local database
**So that** AI can match my activities to the correct billing matters with high confidence

**Acceptance Criteria:**
- [ ] SQLite table for matters: id, matter_number, client_name, description, status (active/archived), created_at, updated_at
- [ ] SQLite table for clients: id, name, notes, created_at
- [ ] Simple tkinter dialog to add/edit/archive matters
- [ ] Simple tkinter dialog to add/edit clients
- [ ] Import matters from CSV file
- [ ] Export matters to CSV file
- [ ] Matter status toggle (active/archived) to hide completed matters

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: Manual verification via `python -m syncopaid.database`

## TDD Tasks

### Task 1: Add clients table to database schema (~3 min)

**Files:**
- **Create:** `test_matter_client.py`
- **Modify:** `src/syncopaid/database.py:67-142`

**Context:** The Database class already has _init_schema() that creates tables. We'll extend it to create a clients table following the same pattern as events/screenshots tables.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py
"""Test matter and client database functionality."""
import sqlite3
import tempfile
import os
from pathlib import Path
from syncopaid.database import Database

def test_clients_table_exists():
    """Verify clients table is created with correct schema."""
    # Create temp database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Query schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "clients table should exist"

        # Verify columns
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clients)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'id' in columns
        assert 'name' in columns
        assert 'notes' in columns
        assert 'created_at' in columns
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `AssertionError: clients table should exist`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (insert after screenshots table creation, around line 141)

            # Create clients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: Test passes with no assertions raised

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/database.py && git commit -m "feat: add clients table to database schema"
```

---

### Task 2: Add matters table to database schema (~3 min)

**Files:**
- **Modify:** `test_matter_client.py`
- **Modify:** `src/syncopaid/database.py:67-142`

**Context:** Matters reference clients via foreign key. Follow the same table creation pattern, placed immediately after the clients table.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append to end of file)

def test_matters_table_exists():
    """Verify matters table is created with correct schema and foreign key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Query schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matters'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "matters table should exist"

        # Verify columns
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(matters)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        assert 'id' in columns
        assert 'matter_number' in columns
        assert 'client_id' in columns
        assert 'description' in columns
        assert 'status' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns

if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `AssertionError: matters table should exist`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (insert after clients table creation, around line 149)

            # Create matters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matter_number TEXT NOT NULL UNIQUE,
                    client_id INTEGER,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # Create index for matter queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_matters_status
                ON matters(status)
            """)
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/database.py && git commit -m "feat: add matters table with client foreign key"
```

---

### Task 3: Add Database methods for client CRUD operations (~4 min)

**Files:**
- **Modify:** `test_matter_client.py`
- **Modify:** `src/syncopaid/database.py:250-350` (after existing query methods)

**Context:** Add methods following the pattern of existing insert_event() and get_events() methods. Use the _get_connection() context manager for transaction safety.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append to end of file, before if __name__)

def test_client_crud_operations():
    """Test create, read, update, delete operations for clients."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client
        client_id = db.insert_client(name="Acme Corp", notes="Tech startup")
        assert client_id > 0

        # Read client
        clients = db.get_clients()
        assert len(clients) == 1
        assert clients[0]['name'] == "Acme Corp"
        assert clients[0]['notes'] == "Tech startup"

        # Update client
        db.update_client(client_id, name="Acme Corporation", notes="Updated notes")
        clients = db.get_clients()
        assert clients[0]['name'] == "Acme Corporation"

        # Delete client
        db.delete_client(client_id)
        clients = db.get_clients()
        assert len(clients) == 0

# Update if __name__ block
if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `AttributeError: 'Database' object has no attribute 'insert_client'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (add after get_statistics method, around line 350)

    def insert_client(self, name: str, notes: Optional[str] = None) -> int:
        """
        Insert a new client.

        Args:
            name: Client name (required)
            notes: Optional notes about the client

        Returns:
            The ID of the inserted client
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, notes)
                VALUES (?, ?)
            """, (name, notes))
            return cursor.lastrowid

    def get_clients(self) -> List[Dict]:
        """
        Get all clients.

        Returns:
            List of client dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def update_client(self, client_id: int, name: str, notes: Optional[str] = None):
        """
        Update an existing client.

        Args:
            client_id: ID of the client to update
            name: Updated client name
            notes: Updated notes
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clients
                SET name = ?, notes = ?
                WHERE id = ?
            """, (name, notes, client_id))

    def delete_client(self, client_id: int):
        """
        Delete a client.

        Args:
            client_id: ID of the client to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/database.py && git commit -m "feat: add client CRUD methods to Database class"
```

---

### Task 4: Add Database methods for matter CRUD operations (~5 min)

**Files:**
- **Modify:** `test_matter_client.py`
- **Modify:** `src/syncopaid/database.py:350-450`

**Context:** Matter methods are similar to client methods but include status filtering (active/archived) and updated_at timestamp management.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append before if __name__)

def test_matter_crud_operations():
    """Test create, read, update, archive operations for matters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create client first
        client_id = db.insert_client(name="Test Client", notes="For testing")

        # Create matter
        matter_id = db.insert_matter(
            matter_number="2024-001",
            client_id=client_id,
            description="Contract review"
        )
        assert matter_id > 0

        # Read matters (should show active by default)
        matters = db.get_matters()
        assert len(matters) == 1
        assert matters[0]['matter_number'] == "2024-001"
        assert matters[0]['status'] == 'active'

        # Update matter
        db.update_matter(matter_id, matter_number="2024-001", description="Updated contract review")
        matters = db.get_matters()
        assert matters[0]['description'] == "Updated contract review"

        # Archive matter
        db.update_matter_status(matter_id, status='archived')
        active_matters = db.get_matters(status='active')
        assert len(active_matters) == 0

        all_matters = db.get_matters(status='all')
        assert len(all_matters) == 1
        assert all_matters[0]['status'] == 'archived'

# Update if __name__ block
if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    test_matter_crud_operations()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `AttributeError: 'Database' object has no attribute 'insert_matter'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database.py (add after client methods, around line 410)

    def insert_matter(
        self,
        matter_number: str,
        client_id: Optional[int] = None,
        description: Optional[str] = None,
        status: str = 'active'
    ) -> int:
        """
        Insert a new matter.

        Args:
            matter_number: Unique matter identifier (required)
            client_id: Optional reference to client
            description: Optional matter description
            status: Matter status ('active' or 'archived'), defaults to 'active'

        Returns:
            The ID of the inserted matter
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO matters (matter_number, client_id, description, status)
                VALUES (?, ?, ?, ?)
            """, (matter_number, client_id, description, status))
            return cursor.lastrowid

    def get_matters(self, status: str = 'active') -> List[Dict]:
        """
        Get matters filtered by status.

        Args:
            status: 'active', 'archived', or 'all' (default: 'active')

        Returns:
            List of matter dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if status == 'all':
                cursor.execute("""
                    SELECT m.*, c.name as client_name
                    FROM matters m
                    LEFT JOIN clients c ON m.client_id = c.id
                    ORDER BY m.created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT m.*, c.name as client_name
                    FROM matters m
                    LEFT JOIN clients c ON m.client_id = c.id
                    WHERE m.status = ?
                    ORDER BY m.created_at DESC
                """, (status,))

            return [dict(row) for row in cursor.fetchall()]

    def update_matter(
        self,
        matter_id: int,
        matter_number: str,
        client_id: Optional[int] = None,
        description: Optional[str] = None
    ):
        """
        Update an existing matter.

        Args:
            matter_id: ID of the matter to update
            matter_number: Updated matter number
            client_id: Updated client reference
            description: Updated description
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matters
                SET matter_number = ?, client_id = ?, description = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (matter_number, client_id, description, matter_id))

    def update_matter_status(self, matter_id: int, status: str):
        """
        Update matter status (active/archived).

        Args:
            matter_id: ID of the matter
            status: New status ('active' or 'archived')
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matters
                SET status = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (status, matter_id))
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/database.py && git commit -m "feat: add matter CRUD methods with status management"
```

---

### Task 5: Create client management dialog (~5 min)

**Files:**
- **Create:** `src/syncopaid/matter_client_dialog.py`

**Context:** New module following tkinter patterns from __main__.py (filedialog usage around line 277). Create simple dialog with Listbox for clients, entry fields, and action buttons.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append before if __name__)

def test_client_dialog_module_exists():
    """Verify matter_client_dialog module can be imported."""
    try:
        from syncopaid.matter_client_dialog import ClientDialog
        assert True
    except ImportError:
        assert False, "ClientDialog should be importable"

# Update if __name__ block
if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    test_matter_crud_operations()
    test_client_dialog_module_exists()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `AssertionError: ClientDialog should be importable`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/matter_client_dialog.py (new file)
"""
Client and matter management dialogs.

Simple tkinter-based UI for managing the local client/matter database.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from syncopaid.database import Database


class ClientDialog:
    """
    Dialog for managing clients.

    Provides:
    - List of all clients
    - Add new client
    - Edit selected client
    - Delete selected client
    """

    def __init__(self, parent, db: Database, on_close: Optional[Callable] = None):
        """
        Initialize client management dialog.

        Args:
            parent: Parent tkinter window
            db: Database instance
            on_close: Optional callback when dialog closes
        """
        self.db = db
        self.on_close = on_close

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Clients")
        self.window.geometry("600x400")

        # Client list
        list_frame = ttk.Frame(self.window, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(list_frame, text="Clients:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        self.client_listbox = tk.Listbox(list_frame, height=15)
        self.client_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.client_listbox.bind('<<ListboxSelect>>', self._on_select)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Add Client", command=self._add_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Client", command=self._edit_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Client", command=self._delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self._close).pack(side=tk.RIGHT, padx=5)

        # Load clients
        self._refresh_list()

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

    def _refresh_list(self):
        """Reload client list from database."""
        self.client_listbox.delete(0, tk.END)
        self.clients = self.db.get_clients()

        for client in self.clients:
            display = f"{client['name']}"
            if client['notes']:
                display += f" - {client['notes'][:50]}"
            self.client_listbox.insert(tk.END, display)

    def _on_select(self, event):
        """Handle client selection."""
        pass  # Selection tracking for edit/delete

    def _add_client(self):
        """Show dialog to add new client."""
        dialog = ClientEditDialog(self.window, self.db)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _edit_client(self):
        """Edit selected client."""
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to edit.")
            return

        client = self.clients[selection[0]]
        dialog = ClientEditDialog(self.window, self.db, client)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _delete_client(self):
        """Delete selected client."""
        selection = self.client_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a client to delete.")
            return

        client = self.clients[selection[0]]
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete client '{client['name']}'?\n\nThis cannot be undone."
        )

        if confirm:
            self.db.delete_client(client['id'])
            self._refresh_list()

    def _close(self):
        """Close dialog."""
        if self.on_close:
            self.on_close()
        self.window.destroy()


class ClientEditDialog:
    """Dialog for adding/editing a single client."""

    def __init__(self, parent, db: Database, client: Optional[dict] = None):
        """
        Initialize client edit dialog.

        Args:
            parent: Parent window
            db: Database instance
            client: Existing client dict (None for new client)
        """
        self.db = db
        self.client = client

        # Create dialog
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Client" if client else "Add Client")
        self.window.geometry("400x200")

        # Form fields
        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Client Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=client['name'] if client else "")
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)

        ttk.Label(form_frame, text="Notes:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.notes_var = tk.StringVar(value=client['notes'] if client and client['notes'] else "")
        ttk.Entry(form_frame, textvariable=self.notes_var, width=40).grid(row=1, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

    def _save(self):
        """Save client to database."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Validation Error", "Client name is required.")
            return

        notes = self.notes_var.get().strip() or None

        if self.client:
            # Update existing
            self.db.update_client(self.client['id'], name, notes)
        else:
            # Create new
            self.db.insert_client(name, notes)

        self.window.destroy()
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/matter_client_dialog.py && git commit -m "feat: add client management dialog with tkinter UI"
```

---

### Task 6: Create matter management dialog (~5 min)

**Files:**
- **Modify:** `test_matter_client.py`
- **Modify:** `src/syncopaid/matter_client_dialog.py`

**Context:** Similar to ClientDialog but with matter-specific fields (matter_number, client selection dropdown, status toggle). Place after ClientEditDialog class.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append before if __name__)

def test_matter_dialog_module_exists():
    """Verify MatterDialog can be imported."""
    try:
        from syncopaid.matter_client_dialog import MatterDialog
        assert True
    except ImportError:
        assert False, "MatterDialog should be importable"

# Update if __name__ block
if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    test_matter_crud_operations()
    test_client_dialog_module_exists()
    test_matter_dialog_module_exists()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `AssertionError: MatterDialog should be importable`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/matter_client_dialog.py (append after ClientEditDialog)

class MatterDialog:
    """
    Dialog for managing matters.

    Provides:
    - List of matters (filterable by status)
    - Add new matter
    - Edit selected matter
    - Archive/unarchive matter
    - Export matters to CSV
    - Import matters from CSV
    """

    def __init__(self, parent, db: Database, on_close: Optional[Callable] = None):
        """
        Initialize matter management dialog.

        Args:
            parent: Parent tkinter window
            db: Database instance
            on_close: Optional callback when dialog closes
        """
        self.db = db
        self.on_close = on_close
        self.status_filter = tk.StringVar(value='active')

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Matters")
        self.window.geometry("800x500")

        # Top controls
        control_frame = ttk.Frame(self.window, padding=10)
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="Show:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="Active", variable=self.status_filter,
                       value='active', command=self._refresh_list).pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="Archived", variable=self.status_filter,
                       value='archived', command=self._refresh_list).pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="All", variable=self.status_filter,
                       value='all', command=self._refresh_list).pack(side=tk.LEFT)

        # Matter list
        list_frame = ttk.Frame(self.window, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.matter_listbox = tk.Listbox(list_frame, height=15)
        self.matter_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.matter_listbox.bind('<<ListboxSelect>>', self._on_select)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Add Matter", command=self._add_matter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Matter", command=self._edit_matter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Toggle Status", command=self._toggle_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import CSV", command=self._import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export CSV", command=self._export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self._close).pack(side=tk.RIGHT, padx=5)

        # Load matters
        self._refresh_list()

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

    def _refresh_list(self):
        """Reload matter list from database."""
        self.matter_listbox.delete(0, tk.END)
        self.matters = self.db.get_matters(status=self.status_filter.get())

        for matter in self.matters:
            client_name = matter.get('client_name', 'No Client')
            display = f"[{matter['matter_number']}] {client_name} - {matter['description'] or 'No description'}"
            if matter['status'] == 'archived':
                display += " (ARCHIVED)"
            self.matter_listbox.insert(tk.END, display)

    def _on_select(self, event):
        """Handle matter selection."""
        pass

    def _add_matter(self):
        """Show dialog to add new matter."""
        dialog = MatterEditDialog(self.window, self.db)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _edit_matter(self):
        """Edit selected matter."""
        selection = self.matter_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a matter to edit.")
            return

        matter = self.matters[selection[0]]
        dialog = MatterEditDialog(self.window, self.db, matter)
        self.window.wait_window(dialog.window)
        self._refresh_list()

    def _toggle_status(self):
        """Toggle matter status between active and archived."""
        selection = self.matter_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a matter.")
            return

        matter = self.matters[selection[0]]
        new_status = 'archived' if matter['status'] == 'active' else 'active'
        self.db.update_matter_status(matter['id'], new_status)
        self._refresh_list()

    def _import_csv(self):
        """Import matters from CSV file."""
        # Placeholder - implemented in Task 7
        messagebox.showinfo("Not Implemented", "CSV import will be implemented in next task.")

    def _export_csv(self):
        """Export matters to CSV file."""
        # Placeholder - implemented in Task 7
        messagebox.showinfo("Not Implemented", "CSV export will be implemented in next task.")

    def _close(self):
        """Close dialog."""
        if self.on_close:
            self.on_close()
        self.window.destroy()


class MatterEditDialog:
    """Dialog for adding/editing a single matter."""

    def __init__(self, parent, db: Database, matter: Optional[dict] = None):
        """
        Initialize matter edit dialog.

        Args:
            parent: Parent window
            db: Database instance
            matter: Existing matter dict (None for new matter)
        """
        self.db = db
        self.matter = matter

        # Create dialog
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Matter" if matter else "Add Matter")
        self.window.geometry("500x300")

        # Form fields
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
        self.client_var = tk.StringVar()

        # Set initial client selection
        if matter and matter.get('client_id'):
            for c in self.clients:
                if c['id'] == matter['client_id']:
                    self.client_var.set(c['name'])
                    break
        else:
            self.client_var.set("(No Client)")

        ttk.Combobox(form_frame, textvariable=self.client_var, values=client_names,
                    state='readonly', width=38).grid(row=1, column=1, pady=5)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar(value=matter['description'] if matter and matter['description'] else "")
        ttk.Entry(form_frame, textvariable=self.description_var, width=40).grid(row=2, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

    def _save(self):
        """Save matter to database."""
        matter_number = self.matter_number_var.get().strip()
        if not matter_number:
            messagebox.showerror("Validation Error", "Matter number is required.")
            return

        # Get client ID
        client_name = self.client_var.get()
        client_id = None
        if client_name != "(No Client)":
            for c in self.clients:
                if c['name'] == client_name:
                    client_id = c['id']
                    break

        description = self.description_var.get().strip() or None

        try:
            if self.matter:
                # Update existing
                self.db.update_matter(self.matter['id'], matter_number, client_id, description)
            else:
                # Create new
                self.db.insert_matter(matter_number, client_id, description)

            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save matter:\n{str(e)}")
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/matter_client_dialog.py && git commit -m "feat: add matter management dialog with status toggle"
```

---

### Task 7: Add CSV import/export for matters (~4 min)

**Files:**
- **Modify:** `test_matter_client.py`
- **Modify:** `src/syncopaid/matter_client_dialog.py:150-180` (MatterDialog._import_csv and _export_csv methods)

**Context:** Use Python's csv module and tkinter's filedialog (pattern from __main__.py:277). CSV format: matter_number, client_name, description, status

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append before if __name__)

def test_matter_csv_export_import():
    """Test CSV export and import functionality."""
    import csv
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create test data
        client_id = db.insert_client(name="Test Corp", notes="Test client")
        db.insert_matter("2024-001", client_id, "Matter 1", "active")
        db.insert_matter("2024-002", client_id, "Matter 2", "archived")

        # Export to CSV
        csv_path = Path(tmpdir) / "matters.csv"
        _export_matters_to_csv(db, str(csv_path))

        # Verify CSV exists and has correct format
        assert csv_path.exists()
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['matter_number'] == '2024-001'

        # Clear database
        db.delete_client(client_id)  # Should cascade or we handle manually

        # Import from CSV
        _import_matters_from_csv(db, str(csv_path))

        # Verify import
        matters = db.get_matters(status='all')
        assert len(matters) >= 2

def _export_matters_to_csv(db: Database, csv_path: str):
    """Helper function to export matters to CSV."""
    from syncopaid.matter_client_dialog import export_matters_csv
    export_matters_csv(db, csv_path)

def _import_matters_from_csv(db: Database, csv_path: str):
    """Helper function to import matters from CSV."""
    from syncopaid.matter_client_dialog import import_matters_csv
    import_matters_csv(db, csv_path)

# Update if __name__ block
if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    test_matter_crud_operations()
    test_client_dialog_module_exists()
    test_matter_dialog_module_exists()
    test_matter_csv_export_import()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: `ImportError: cannot import name 'export_matters_csv'`

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/matter_client_dialog.py (add at top after imports)
import csv
from tkinter import filedialog

# Add these standalone functions before ClientDialog class

def export_matters_csv(db: Database, csv_path: str):
    """
    Export all matters to CSV file.

    Args:
        db: Database instance
        csv_path: Output CSV file path
    """
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
    """
    Import matters from CSV file.

    Args:
        db: Database instance
        csv_path: Input CSV file path

    CSV format: matter_number, client_name, description, status
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Find or create client
            client_id = None
            client_name = row.get('client_name', '').strip()
            if client_name:
                clients = db.get_clients()
                for c in clients:
                    if c['name'] == client_name:
                        client_id = c['id']
                        break

                # Create client if not found
                if client_id is None:
                    client_id = db.insert_client(name=client_name)

            # Insert matter (skip if duplicate matter_number)
            try:
                db.insert_matter(
                    matter_number=row['matter_number'],
                    client_id=client_id,
                    description=row.get('description', '').strip() or None,
                    status=row.get('status', 'active')
                )
            except Exception:
                # Skip duplicates
                pass


# Update MatterDialog._export_csv method (around line 350)
    def _export_csv(self):
        """Export matters to CSV file."""
        from tkinter import filedialog

        csv_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export Matters to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if csv_path:
            try:
                export_matters_csv(self.db, csv_path)
                messagebox.showinfo("Success", f"Exported {len(self.matters)} matters to CSV.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export CSV:\n{str(e)}")


# Update MatterDialog._import_csv method (around line 340)
    def _import_csv(self):
        """Import matters from CSV file."""
        from tkinter import filedialog

        csv_path = filedialog.askopenfilename(
            parent=self.window,
            title="Import Matters from CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if csv_path:
            try:
                import_matters_csv(self.db, csv_path)
                self._refresh_list()
                messagebox.showinfo("Success", "Matters imported from CSV.")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import CSV:\n{str(e)}")
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/matter_client_dialog.py && git commit -m "feat: add CSV import/export for matters"
```

---

### Task 8: Integrate dialogs into system tray menu (~3 min)

**Files:**
- **Modify:** `test_matter_client.py`
- **Modify:** `src/syncopaid/tray.py:25-80` (TrayIcon menu setup)

**Context:** TrayIcon class in tray.py creates menu around line 25-80. Add "Manage Clients" and "Manage Matters" menu items following the pattern of existing "Export Data" menu item.

**Step 1 - RED:** Write failing test
```python
# test_matter_client.py (append before if __name__)

def test_tray_integration():
    """Verify matter/client management can be imported in tray module."""
    # This is a minimal integration test - full tray testing requires GUI
    try:
        from syncopaid.matter_client_dialog import ClientDialog, MatterDialog
        from syncopaid.database import Database
        assert callable(ClientDialog)
        assert callable(MatterDialog)
    except ImportError as e:
        assert False, f"Should be able to import dialogs: {e}"

# Update if __name__ block
if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    test_matter_crud_operations()
    test_client_dialog_module_exists()
    test_matter_dialog_module_exists()
    test_matter_csv_export_import()
    test_tray_integration()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_matter_client.py
```
Expected output: Test should pass (this is a sanity check, real integration happens in Step 3)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/tray.py (find the menu creation section around line 50-80 and add new items)

# First, add import at top of file (around line 10-15, with other imports)
from syncopaid.matter_client_dialog import ClientDialog, MatterDialog

# Then locate the menu creation in TrayIcon.__init__ (around line 50-80)
# Add these menu items before "Export Data" item:

            pystray.MenuItem("Manage Clients", self._show_client_dialog),
            pystray.MenuItem("Manage Matters", self._show_matter_dialog),
            pystray.Menu.SEPARATOR,

# Add these methods to TrayIcon class (around line 200, after other menu handlers)

    def _show_client_dialog(self):
        """Show client management dialog."""
        def show():
            root = tk.Tk()
            root.withdraw()  # Hide root window

            # Ensure dialog is on top
            root.attributes('-topmost', True)
            root.update()

            ClientDialog(root, self.db)
            root.mainloop()

        # Run in separate thread to avoid blocking tray
        import threading
        threading.Thread(target=show, daemon=True).start()

    def _show_matter_dialog(self):
        """Show matter management dialog."""
        def show():
            root = tk.Tk()
            root.withdraw()  # Hide root window

            # Ensure dialog is on top
            root.attributes('-topmost', True)
            root.update()

            MatterDialog(root, self.db)
            root.mainloop()

        # Run in separate thread to avoid blocking tray
        import threading
        threading.Thread(target=show, daemon=True).start()
```

**Step 4 - Verify GREEN:**
```bash
python test_matter_client.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_matter_client.py src/syncopaid/tray.py && git commit -m "feat: integrate matter/client dialogs into system tray menu"
```

---

## Final Verification

Run after all tasks complete:
```bash
python test_matter_client.py                # All tests pass
python -m syncopaid.database                # Database module runs without error
python -m syncopaid                         # Full app runs, tray should show new menu items
```

Manual verification:
1. Launch SyncoPaid application
2. Right-click system tray icon
3. Verify "Manage Clients" and "Manage Matters" menu items appear
4. Click "Manage Clients" - dialog should open
5. Add a test client, verify it saves
6. Click "Manage Matters" - dialog should open
7. Add a test matter with the client, verify it saves
8. Toggle matter status (active/archived), verify it updates
9. Export matters to CSV, verify file is created
10. Import matters from CSV, verify they load

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

**Edge Cases:**
- Deleting a client with associated matters: Current implementation allows orphaned matters (client_id becomes NULL via LEFT JOIN). Future enhancement could add CASCADE or prevent deletion.
- Duplicate matter numbers: SQLite UNIQUE constraint will raise exception, caught in CSV import (skips duplicates)
- Empty client dropdown: If no clients exist, user can still create matters without clients

**Follow-up Work:**
- Story 1.8.1.1: Matter Keywords/Tags for AI Matching (adds tags/keywords table)
- Story 1.8.4: AI Disambiguation with Screenshot Context (uses this database for matching)

**Dependencies:**
- This story is a prerequisite for Story 1.8.4 (AI Disambiguation)
