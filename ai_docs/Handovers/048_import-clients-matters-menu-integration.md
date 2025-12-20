# 048: Import Clients & Matters - Menu Integration

## Task
Wire up the "Import Clients & Matters" menu item to the main window File menu.

## Context
This is the final integration task. The import dialog (047), folder parser (046), and database schema (045) are complete. Now wire them together through the menu.

## Scope
- Add menu item to File menu in main window
- Add callback in `SyncoPaidApp` class
- Connect dialog to database for actual saving

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_ui_windows.py` | Lines 148-160 - File menu definition |
| `src/syncopaid/__main__.py` | `SyncoPaidApp` class - add callback |

## Changes to main_ui_windows.py

In `show_main_window()`, find the File menu section (around line 148-160):

```python
# File menu with Exit
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)

# ADD THIS:
def import_clients_matters():
    show_import_dialog(database)

file_menu.add_command(label="Import Clients && Matters...", command=import_clients_matters)
file_menu.add_separator()  # Optional: add separator before Exit

def exit_program():
    # ... existing code
```

Note: Use `&&` in tkinter menu labels to display a single `&`.

## Changes to __main__.py

Add method to `SyncoPaidApp` class for external access:

```python
def show_import_dialog(self):
    """Show dialog for importing client/matter data."""
    from syncopaid.main_ui_windows import show_import_dialog
    show_import_dialog(self.database)
```

## Updated show_import_dialog Signature

Update `show_import_dialog()` to accept and use database:

```python
def show_import_dialog(database):
    """Show dialog for importing client/matter data from folder structure."""

    def run_dialog():
        # ... existing dialog code ...

        def do_import():
            if not import_result or not import_result.matters:
                messagebox.showwarning("No Data", "No matters to import.", parent=root)
                return

            try:
                save_import_to_database(database, import_result)
                count = len(import_result.matters)
                messagebox.showinfo("Import Complete",
                    f"Imported {count} matters.", parent=root)
                root.destroy()
            except Exception as e:
                logging.error(f"Import failed: {e}", exc_info=True)
                messagebox.showerror("Import Failed",
                    f"Error: {str(e)}", parent=root)

        # ... rest of dialog ...
```

## Full Integration Checklist

1. [ ] Database schema created (task 045)
2. [ ] Folder parser module created (task 046)
3. [ ] Import dialog created (task 047)
4. [ ] Menu item added to File menu
5. [ ] `save_import_to_database()` function implemented
6. [ ] Database passed to dialog
7. [ ] Error handling for import failures

## Menu Structure After Changes

```
File
├── Import Clients & Matters...  ← NEW
├── ─── (separator)
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
5. Preview populates
6. Click Import
7. Verify data in database:
   ```bash
   sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" "SELECT * FROM clients;"
   sqlite3 "%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db" "SELECT * FROM matters;"
   ```

## Error Cases to Test

- Empty folder (no subfolders)
- Folder with only 1 level (clients but no matters)
- Permission denied folder
- Cancel mid-browse
- Close dialog with X button

## Dependencies
- All prior tasks (045, 046, 047) must be complete

## Post-Integration

After this task, the feature is complete. Consider:
- Update `CLAUDE.md` with new feature documentation
- Add entry to help/about if applicable
