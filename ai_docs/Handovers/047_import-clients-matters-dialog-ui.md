# 047: Import Clients & Matters - Dialog UI

## Task
Create a single import dialog for selecting a folder and previewing/confirming the import.

## Context
User wants a simple, single-dialog experience (not a wizard). User selects folder → sees preview of extracted clients/matters → confirms import.

## Scope
- Add `show_import_dialog()` function to `main_ui_windows.py`
- Single dialog with folder selection + preview table + import button
- Thread-safe (run in daemon thread like other dialogs)

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_ui_windows.py` | Add dialog here (lines 36-96 show export pattern) |
| `src/syncopaid/client_matter_importer.py` | Import logic (from task 046) |
| `src/syncopaid/database.py` | Database for saving imported data |

## Dialog Pattern

Follow `show_export_dialog()` at lines 36-96:
```python
def show_import_dialog(database):
    def run_dialog():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        # ... dialog logic ...
        root.destroy()

    dialog_thread = threading.Thread(target=run_dialog, daemon=True)
    dialog_thread.start()
```

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│ Import Clients & Matters                            │
├─────────────────────────────────────────────────────┤
│ Folder: [________________________] [Browse...]      │
├─────────────────────────────────────────────────────┤
│ Preview (X clients, Y matters found)                │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Client Name    │ Client # │ Matter Name │ Mat # │ │
│ │────────────────┼──────────┼─────────────┼───────│ │
│ │ Smith, John    │ C001     │ Real Estate │ M001  │ │
│ │ Smith, John    │ C001     │ Divorce     │ M002  │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│                              [Cancel]  [Import]     │
└─────────────────────────────────────────────────────┘
```

## Implementation

```python
def show_import_dialog(database):
    """Show dialog for importing client/matter data from folder structure."""

    def run_dialog():
        from syncopaid.client_matter_importer import import_from_folder

        root = tk.Tk()
        root.title("Import Clients & Matters")
        root.geometry("700x450")
        root.attributes('-topmost', True)
        set_window_icon(root)

        # State
        import_result = None

        # Folder selection frame
        folder_frame = tk.Frame(root, pady=10, padx=10)
        folder_frame.pack(fill=tk.X)

        tk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        folder_var = tk.StringVar()
        folder_entry = tk.Entry(folder_frame, textvariable=folder_var, width=50)
        folder_entry.pack(side=tk.LEFT, padx=5)

        def browse_folder():
            nonlocal import_result
            path = filedialog.askdirectory(parent=root, title="Select Client Folder")
            if path:
                folder_var.set(path)
                # Parse and preview
                import_result = import_from_folder(path)
                update_preview()

        tk.Button(folder_frame, text="Browse...", command=browse_folder).pack(side=tk.LEFT)

        # Preview label
        preview_label = tk.Label(root, text="Select a folder to preview", pady=5)
        preview_label.pack()

        # Treeview for preview
        columns = ('client_name', 'client_no', 'matter_name', 'matter_no')
        tree = ttk.Treeview(root, columns=columns, show='headings', height=12)
        tree.heading('client_name', text='Client Name')
        tree.heading('client_no', text='Client #')
        tree.heading('matter_name', text='Matter Name')
        tree.heading('matter_no', text='Matter #')

        tree.column('client_name', width=180)
        tree.column('client_no', width=80)
        tree.column('matter_name', width=200)
        tree.column('matter_no', width=80)

        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        def update_preview():
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)

            if import_result:
                preview_label.config(
                    text=f"Found {len(import_result.clients)} clients, "
                         f"{len(import_result.matters)} matters"
                )
                for m in import_result.matters:
                    tree.insert('', tk.END, values=(
                        m.client_name, m.client_no or '',
                        m.matter_name, m.matter_no or ''
                    ))

        # Button frame
        btn_frame = tk.Frame(root, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def do_import():
            if not import_result or not import_result.matters:
                messagebox.showwarning("No Data", "No matters to import.", parent=root)
                return

            # TODO: Save to database (task 048 will wire this up)
            count = len(import_result.matters)
            messagebox.showinfo("Import Complete", f"Imported {count} matters.", parent=root)
            root.destroy()

        tk.Button(btn_frame, text="Cancel", command=root.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Import", command=do_import, width=10).pack(side=tk.RIGHT, padx=5)

        root.mainloop()

    dialog_thread = threading.Thread(target=run_dialog, daemon=True)
    dialog_thread.start()
```

## Database Save Logic

After preview confirmation, save to database:
```python
def save_import_to_database(database, import_result):
    """Save imported clients and matters to database."""
    with database._get_connection() as conn:
        cursor = conn.cursor()

        # Insert clients
        client_ids = {}
        for client in import_result.clients:
            cursor.execute("""
                INSERT OR IGNORE INTO clients (client_no, client_name, folder_path, confidence)
                VALUES (?, ?, ?, ?)
            """, (client.client_no, client.client_name, client.folder_path, client.confidence))

            # Get ID (existing or new)
            cursor.execute(
                "SELECT id FROM clients WHERE client_name = ? AND (client_no = ? OR client_no IS NULL)",
                (client.client_name, client.client_no)
            )
            client_ids[client.client_name] = cursor.fetchone()[0]

        # Insert matters
        for matter in import_result.matters:
            client_id = client_ids.get(matter.client_name)
            if client_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO matters
                    (client_id, matter_no, matter_name, folder_path, confidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (client_id, matter.matter_no, matter.matter_name,
                      matter.folder_path, matter.confidence))

        conn.commit()
```

## Verification

```bash
venv\Scripts\activate
python -c "from syncopaid.main_ui_windows import show_import_dialog; show_import_dialog(None)"
```

## Dependencies
- Task 045 (database schema)
- Task 046 (folder parser)

## Next Task
After this: `048_import-clients-matters-menu-integration.md`
