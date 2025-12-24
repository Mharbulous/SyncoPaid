# 022E-B: Assignment Dialog and Double-Click Binding
Story ID: 8.1.2

## Task
Create the client/matter assignment dialog and wire it to double-click on treeview rows.

## Context
This is part B of the time assignment UI implementation. With columns added in 022E-A, users now need a way to edit client/matter assignments.

## Scope
1. Create `show_assignment_dialog` function with client/matter dropdowns
2. Wire double-click binding on treeview to open dialog

## Implementation Details

### Task 1: Create Assignment Dialog

Add function to `src/syncopaid/main_ui_windows.py`:

```python
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
```

### Task 2: Wire Double-Click Binding

In `show_main_window()`, add binding to treeview:

```python
def on_double_click(event):
    selection = tree.selection()
    if not selection:
        return
    item = tree.item(selection[0])
    values = item['values']
    event_id = values[0]
    current_client = values[6] if len(values) > 6 else ''
    current_matter = values[7] if len(values) > 7 else ''

    def on_save(client, matter):
        # Update treeview
        tree.set(selection[0], 'client', client or '')
        tree.set(selection[0], 'matter', matter or '')

    show_assignment_dialog(database, event_id, current_client, current_matter, on_save)

tree.bind('<Double-1>', on_double_click)
```

## Verification
```bash
venv\Scripts\activate
python -m syncopaid
```

1. Import some clients/matters (File → Import)
2. Open main window
3. Double-click an event row
4. Verify dialog appears with Client/Matter dropdowns
5. Select client, verify matters filter correctly
6. Click Save, verify treeview updates
7. Verify database:
   ```bash
   sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" \
     "SELECT id, client, matter FROM events WHERE client IS NOT NULL;"
   ```

## Dependencies
- 022E-A complete (treeview columns exist)
- Tasks 022A-022D complete (import functionality)
