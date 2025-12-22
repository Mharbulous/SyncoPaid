# 022C2: Import Clients & Matters - Dialog UI
Story ID: 8.1.2

## Task
Create the tkinter dialog for selecting a folder and previewing/confirming the import.

## Context
User selects folder -> sees preview of extracted clients/matters -> confirms import. Single dialog, no wizard.

## Scope
- Add `show_import_dialog()` function to `main_ui_windows.py`
- Single dialog with folder selection + preview table + import button
- Thread-safe (run in daemon thread like other dialogs)
- Uses `save_import_to_database()` from 022C1

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_ui_windows.py` | Add dialog here (lines 36-96 show export pattern) |
| `src/syncopaid/client_matter_importer.py` | Import logic (from task 022B) |

## Dialog Pattern

Follow `show_export_dialog()` at lines 36-96:
```python
def show_import_dialog(database):
    def run_dialog():
        root = tk.Tk()
        root.title("Import Clients & Matters")
        root.geometry("600x400")
        root.attributes('-topmost', True)
        # ... dialog logic ...
        root.mainloop()

    dialog_thread = threading.Thread(target=run_dialog, daemon=True)
    dialog_thread.start()
```

## UI Layout

```
+------------------------------------------------------+
| Import Clients & Matters                             |
+------------------------------------------------------+
| Folder: [____________________________] [Browse...]   |
+------------------------------------------------------+
| Preview (X clients, Y matters)                       |
| +--------------------------------------------------+ |
| | Client              | Matter                     | |
| |---------------------+----------------------------| |
| | Smith, John         | Real Estate Purchase       | |
| | Smith, John         | Divorce Proceedings        | |
| | Johnson Corp        | Contract Dispute           | |
| +--------------------------------------------------+ |
+------------------------------------------------------+
|                               [Cancel]   [Import]    |
+------------------------------------------------------+
```

## TDD Task

### Task 1: Implement show_import_dialog function

**Test First** (structure test only - GUI requires manual verification):
```python
# tests/test_import_dialog.py
import pytest
from unittest.mock import patch, Mock

def test_show_import_dialog_exists():
    """Test that show_import_dialog function exists and is callable."""
    from syncopaid.main_ui_windows import show_import_dialog
    assert callable(show_import_dialog)

def test_show_import_dialog_starts_thread():
    """Test that dialog runs in a daemon thread."""
    with patch('syncopaid.main_ui_windows.threading.Thread') as mock_thread:
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        from syncopaid.main_ui_windows import show_import_dialog
        show_import_dialog(None)

        mock_thread.assert_called_once()
        assert mock_thread.call_args.kwargs.get('daemon') == True
        mock_thread_instance.start.assert_called_once()
```

**Implementation**:
```python
def show_import_dialog(database):
    """Show dialog for importing client/matter data from folder structure."""

    def run_dialog():
        from syncopaid.client_matter_importer import import_from_folder

        root = tk.Tk()
        root.title("Import Clients & Matters")
        root.geometry("600x400")
        root.attributes('-topmost', True)
        set_window_icon(root)

        # State
        import_result = None

        # Folder selection frame
        folder_frame = tk.Frame(root, pady=10, padx=10)
        folder_frame.pack(fill=tk.X)

        tk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        folder_var = tk.StringVar()
        folder_entry = tk.Entry(folder_frame, textvariable=folder_var, width=40)
        folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def browse_folder():
            nonlocal import_result
            path = filedialog.askdirectory(parent=root, title="Select Client Folder")
            if path:
                folder_var.set(path)
                import_result = import_from_folder(path)
                update_preview()

        tk.Button(folder_frame, text="Browse...", command=browse_folder).pack(side=tk.LEFT)

        # Preview label
        preview_label = tk.Label(root, text="Select a folder to preview", pady=5)
        preview_label.pack()

        # Preview frame with treeview
        preview_frame = tk.Frame(root)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        columns = ('client', 'matter')
        tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=10)
        tree.heading('client', text='Client')
        tree.heading('matter', text='Matter')
        tree.column('client', width=200)
        tree.column('matter', width=300)

        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def update_preview():
            for item in tree.get_children():
                tree.delete(item)

            if import_result:
                preview_label.config(
                    text=f"Found {import_result.stats['clients']} clients, "
                         f"{import_result.stats['matters']} matters"
                )
                for m in import_result.matters:
                    tree.insert('', tk.END, values=(
                        m.client_display_name,
                        m.display_name
                    ))

        # Button frame
        btn_frame = tk.Frame(root, pady=10, padx=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def do_import():
            if not import_result or not import_result.clients:
                messagebox.showwarning("No Data",
                    "No clients found in selected folder.", parent=root)
                return

            try:
                save_import_to_database(database, import_result)
                messagebox.showinfo("Import Complete",
                    f"Imported {import_result.stats['clients']} clients and "
                    f"{import_result.stats['matters']} matters.", parent=root)
                root.destroy()
            except Exception as e:
                logging.error(f"Import failed: {e}", exc_info=True)
                messagebox.showerror("Import Failed", str(e), parent=root)

        tk.Button(btn_frame, text="Cancel", command=root.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Import", command=do_import, width=10).pack(side=tk.RIGHT, padx=5)

        root.mainloop()

    dialog_thread = threading.Thread(target=run_dialog, daemon=True)
    dialog_thread.start()
```

## Verification

```bash
venv\Scripts\activate

# Run unit tests
pytest tests/test_import_dialog.py -v

# Manual visual test - dialog opens (pass None for quick test)
python -c "from syncopaid.main_ui_windows import show_import_dialog; show_import_dialog(None); import time; time.sleep(30)"

# Full test with application
python -m syncopaid
# Open main window -> File -> Import Clients & Matters
```

## Dependencies
- Task 022A (database schema)
- Task 022B (folder parser - import_from_folder)
- Task 022C1 (save_import_to_database function)

## Next Task
After this: `022D_import-clients-matters-menu-integration.md`
