# 025: Import Clients & Matters - Menu Integration

## Task
Wire up the "Import Clients & Matters" menu item to the main window File menu.

## Context
This task connects the import dialog (024) to the main window menu. After this, users can import client/matter data from their folder structure.

## Scope
- Add menu item to File menu in main window
- Wire dialog to database

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_ui_windows.py` | Lines 148-160 - File menu definition |

## Changes to main_ui_windows.py

In `show_main_window()`, find the File menu section (around line 148-160):

```python
# File menu with Exit
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)

# ADD THESE LINES:
def open_import_dialog():
    show_import_dialog(database)

file_menu.add_command(label="Import Clients && Matters...", command=open_import_dialog)
file_menu.add_separator()
# END ADDITIONS

def exit_program():
    # ... existing code
```

Note: Use `&&` in tkinter menu labels to display a single `&`.

## Menu Structure After Changes

```
File
├── Import Clients & Matters...  ← NEW
├── ─── (separator)              ← NEW
└── Exit
```

## Verification

```bash
venv\Scripts\activate
python -m syncopaid
```

1. Click tray icon → "Open SyncoPaid"
2. Main window opens
3. File → "Import Clients & Matters..."
4. Browse to folder with client/matter structure
5. Preview populates with folder names
6. Click Import
7. Verify data in database:
   ```bash
   sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" "SELECT * FROM clients;"
   sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" "SELECT * FROM matters;"
   ```

## Error Cases to Test

| Scenario | Expected |
|----------|----------|
| Empty folder | "No clients found" warning |
| Cancel button | Dialog closes, no changes |
| Permission denied folder | Skipped silently |
| Re-import same folder | Duplicates ignored (INSERT OR IGNORE) |

## Dependencies
- Task 022 (database schema)
- Task 023 (folder parser)
- Task 024 (dialog UI)

## Next Task
After this: `026_import-clients-matters-time-assignment-ui.md` (optional—adds dropdowns for assigning time)
