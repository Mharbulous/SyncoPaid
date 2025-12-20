# 006E: Matter/Client Database - System Tray Integration

## Task
Add "Manage Clients" and "Manage Matters" menu items to the system tray.

## Context
Final step for the Matter/Client Database feature. Wires the dialogs created in previous tasks to the system tray menu so users can access them.

## Scope
- Add import for ClientDialog, MatterDialog in tray.py
- Add menu items: "Manage Clients", "Manage Matters"
- Add handler methods that launch dialogs in separate threads

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/tray.py` | Add menu items and handlers |

## Implementation

### Step 1: Add imports

```python
# src/syncopaid/tray.py (add to imports at top)
from syncopaid.matter_client_dialog import ClientDialog, MatterDialog
```

### Step 2: Add menu items

In TrayIcon.__init__, find the menu creation section and add:

```python
# Add before "Export Data" menu item
pystray.MenuItem("Manage Clients", self._show_client_dialog),
pystray.MenuItem("Manage Matters", self._show_matter_dialog),
pystray.Menu.SEPARATOR,
```

### Step 3: Add handler methods

```python
# src/syncopaid/tray.py (add to TrayIcon class)
def _show_client_dialog(self):
    """Show client management dialog."""
    def show():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        ClientDialog(root, self.db)
        root.mainloop()

    import threading
    threading.Thread(target=show, daemon=True).start()

def _show_matter_dialog(self):
    """Show matter management dialog."""
    def show():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        MatterDialog(root, self.db)
        root.mainloop()

    import threading
    threading.Thread(target=show, daemon=True).start()
```

## Tests

```python
# tests/test_matter_client.py (add)
def test_tray_integration():
    """Verify dialogs can be imported for tray integration."""
    from syncopaid.matter_client_dialog import ClientDialog, MatterDialog
    from syncopaid.database import Database
    assert callable(ClientDialog)
    assert callable(MatterDialog)
```

## Verification

```bash
venv\Scripts\activate
python tests/test_matter_client.py
python -m syncopaid  # Run app, check tray menu
```

Manual testing:
1. Launch SyncoPaid
2. Right-click system tray icon
3. Verify "Manage Clients" and "Manage Matters" appear
4. Click each - dialogs should open
5. Add a client, then a matter linked to that client
6. Export matters to CSV, verify file created
7. Toggle matter status between active/archived

## Dependencies
- Task 006D (matter dialog with CSV)

## Notes
This completes the Matter/Client Database feature (original story 8.1).

All acceptance criteria should now be met:
- SQLite tables for clients and matters
- tkinter dialogs for add/edit/archive
- CSV import/export for matters
- Status toggle (active/archived)
- System tray menu integration
