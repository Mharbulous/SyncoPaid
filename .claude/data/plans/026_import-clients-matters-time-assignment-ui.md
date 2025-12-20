# 026: Import Clients & Matters - Time Assignment UI

## Task
Add client/matter dropdowns to the main window so users can assign tracked time to imported clients and matters.

## Context
After importing client/matter data (tasks 022-025), users need a way to assign their tracked time entries to specific clients and matters. This task adds that capability to the main window.

The `events` table now has `client` and `matter` columns (added in task 022). This task populates those columns via UI interaction.

## Scope
- Add Client and Matter columns to main window treeview
- Add dropdown/combobox UI for selecting client then matter
- Filter matters based on selected client
- Save assignment to database

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_ui_windows.py` | Main window with event list |
| `src/syncopaid/database.py` | Query clients/matters, update events |

## UI Changes

### Main Window Treeview

Add two columns to the event list:

```python
# Before (line ~227):
columns = ('id', 'start', 'duration', 'end', 'app', 'title')

# After:
columns = ('id', 'start', 'duration', 'end', 'app', 'title', 'client', 'matter')

# Add headings:
tree.heading('client', text='Client')
tree.heading('matter', text='Matter')
tree.column('client', width=120, minwidth=80)
tree.column('matter', width=120, minwidth=80)
```

### Assignment UI Options

**Option A: Double-click row to edit** (simpler)
- Double-click event row → opens small dialog with Client/Matter dropdowns

**Option B: Inline comboboxes** (more complex)
- Select row → bottom panel shows Client/Matter comboboxes

Recommend **Option A** for simplicity.

## Edit Dialog Implementation

```python
def show_assignment_dialog(database, event_id, current_client, current_matter, on_save):
    """Show dialog to assign client/matter to an event."""

    def run_dialog():
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

        root.mainloop()

    # Run in current thread (modal dialog)
    run_dialog()
```

## Wiring Double-Click

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

## Query Updates

Update the event query in `show_main_window()` to include client/matter columns:

```python
cursor.execute(
    """SELECT id, timestamp, duration_seconds, end_time, app, title, client, matter
       FROM events
       WHERE timestamp >= ? AND is_idle = 0
       ORDER BY timestamp DESC""",
    (cutoff_iso,)
)
```

## Database Helper Functions

Add to database module or keep in `main_ui_windows.py`:

```python
def get_all_clients(database):
    """Get all client display names."""
    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT display_name FROM clients ORDER BY display_name")
        return [row[0] for row in cursor.fetchall()]

def get_matters_for_client(database, client_display_name):
    """Get matter display names for a client."""
    with database._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.display_name FROM matters m
            JOIN clients c ON m.client_id = c.id
            WHERE c.display_name = ?
            ORDER BY m.display_name
        """, (client_display_name,))
        return [row[0] for row in cursor.fetchall()]
```

## Verification

```bash
venv\Scripts\activate
python -m syncopaid
```

1. Import some clients/matters (File → Import)
2. Open main window
3. Double-click an event row
4. Select client from dropdown
5. Select matter (filtered by client)
6. Click Save
7. Verify event row updates
8. Verify database:
   ```bash
   sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" \
     "SELECT id, client, matter FROM events WHERE client IS NOT NULL;"
   ```

## Dependencies
- Tasks 022-025 must be complete (import functionality)

## Considerations

- **Empty state**: If no clients imported yet, dropdown is empty. Consider showing helpful message.
- **Bulk assignment**: This task handles single-row editing. Bulk selection could be a future enhancement.
- **Persistence**: Client/matter assignments persist in database and survive app restarts.
