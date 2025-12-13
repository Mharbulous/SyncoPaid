# Delete Log Entries Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to select and delete log entries from the View Time window using the 'delete' command.

**Architecture:** Add multi-select to Treeview, add `delete_events_by_ids()` method to Database, extend command handler in View Time window to handle 'delete' command with confirmation dialog.

**Tech Stack:** Python 3.11+, tkinter (ttk.Treeview), SQLite

---

## Task 1: Add `delete_events_by_ids()` method to Database

**Files:**
- Modify: `src\SyncoPaid\database.py:252-293` (after existing `delete_events` method)
- Test: Manual test via Python REPL

**Step 1: Add the new method**

Add after line 293 (after the existing `delete_events` method):

```python
def delete_events_by_ids(self, event_ids: List[int]) -> int:
    """
    Delete specific events by their IDs.

    Args:
        event_ids: List of event IDs to delete

    Returns:
        Number of events deleted
    """
    if not event_ids:
        return 0

    with self._get_connection() as conn:
        cursor = conn.cursor()

        # Use parameterized query with placeholders
        placeholders = ','.join('?' * len(event_ids))
        query = f"DELETE FROM events WHERE id IN ({placeholders})"

        cursor.execute(query, event_ids)
        deleted_count = cursor.rowcount

        logging.warning(f"Deleted {deleted_count} events by ID from database")
        return deleted_count
```

**Step 2: Verify the method works**

Run in Python REPL (from project root with venv activated):
```python
from SyncoPaid.database import Database
import tempfile
import os

# Create temp database
tmpdir = tempfile.mkdtemp()
db = Database(os.path.join(tmpdir, "test.db"))

# Insert test events
from SyncoPaid.tracker import ActivityEvent
events = [
    ActivityEvent(timestamp="2025-12-11T09:00:00", duration_seconds=60, app="test", title="Test 1", is_idle=False),
    ActivityEvent(timestamp="2025-12-11T09:01:00", duration_seconds=60, app="test", title="Test 2", is_idle=False),
    ActivityEvent(timestamp="2025-12-11T09:02:00", duration_seconds=60, app="test", title="Test 3", is_idle=False),
]
for e in events:
    db.insert_event(e)

# Verify 3 events exist
assert len(db.get_events()) == 3

# Delete events 1 and 3
deleted = db.delete_events_by_ids([1, 3])
assert deleted == 2

# Verify only event 2 remains
remaining = db.get_events()
assert len(remaining) == 1
assert remaining[0]['id'] == 2

print("SUCCESS: delete_events_by_ids works correctly")
```

Expected: "SUCCESS: delete_events_by_ids works correctly"

**Step 3: Commit**

```bash
git add src/SyncoPaid/database.py
git commit -m "feat: add delete_events_by_ids() method to Database

Enables deleting specific events by their IDs, required for
the View Time window delete functionality."
```

---

## Task 2: Store event IDs in Treeview rows

**Files:**
- Modify: `src\SyncoPaid\__main__.py:478-495` (event insertion loop)

**Step 1: Modify event query to include ID**

The current query at line 283-301 already returns 'id' in the event dict. No change needed there.

**Step 2: Store event ID in Treeview row**

Change the Treeview columns definition (around line 359) from:

```python
columns = ('start', 'duration', 'end', 'app', 'title')
```

To:

```python
columns = ('id', 'start', 'duration', 'end', 'app', 'title')
```

**Step 3: Add hidden ID column configuration**

After line 365, add column configuration for 'id':

```python
tree.heading('id', text='ID')
tree.column('id', width=0, stretch=False)  # Hidden column
```

**Step 4: Include ID when inserting rows**

Change the event insertion loop (around line 479-495). Update from:

```python
tree.insert('', tk.END, values=(start_ts, dur, end_ts, app, title))
```

To:

```python
tree.insert('', tk.END, values=(event['id'], start_ts, dur, end_ts, app, title))
```

**Step 5: Test manually**

Run the application and open View Time window. The ID column should be hidden but data should still display correctly.

**Step 6: Commit**

```bash
git add src/SyncoPaid/__main__.py
git commit -m "feat: store event ID in Treeview rows (hidden column)

Required for delete functionality to know which database records
to remove."
```

---

## Task 3: Enable multi-select on Treeview

**Files:**
- Modify: `src\SyncoPaid\__main__.py:360` (Treeview creation)

**Step 1: Add selectmode parameter**

Change the Treeview creation (around line 360) from:

```python
tree = ttk.Treeview(root, columns=columns, show='headings')
```

To:

```python
tree = ttk.Treeview(root, columns=columns, show='headings', selectmode='extended')
```

The 'extended' mode allows:
- Click to select single row
- Ctrl+Click to add/remove from selection
- Shift+Click to select range

**Step 2: Test manually**

Run application, open View Time window, verify you can:
- Select single row (click)
- Select multiple rows (Ctrl+click)
- Select range (Shift+click)

**Step 3: Commit**

```bash
git add src/SyncoPaid/__main__.py
git commit -m "feat: enable multi-select on View Time Treeview

Allows selecting multiple log entries for batch deletion using
Ctrl+Click and Shift+Click."
```

---

## Task 4: Add 'delete' command handler

**Files:**
- Modify: `src\SyncoPaid\__main__.py:378-438` (execute_command function)

**Step 1: Add delete command handling**

In the `execute_command` function, after the quit command check (around line 397), add:

```python
# Check for delete command
if command == "delete":
    # Get selected items
    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection",
            "Please select one or more entries to delete.",
            parent=root
        )
        command_entry.delete(0, tk.END)
        return

    # Get event IDs from selected rows
    event_ids = []
    for item in selected:
        values = tree.item(item, 'values')
        event_id = int(values[0])  # ID is first column
        event_ids.append(event_id)

    # Confirm deletion
    count = len(event_ids)
    confirm = messagebox.askyesno(
        "Confirm Deletion",
        f"Delete {count} selected {'entry' if count == 1 else 'entries'}?\n\n"
        f"This action cannot be undone.",
        parent=root
    )

    if not confirm:
        command_entry.delete(0, tk.END)
        return

    # Delete from database
    deleted = self.database.delete_events_by_ids(event_ids)
    logging.info(f"Deleted {deleted} events via delete command")

    # Remove from Treeview
    for item in selected:
        tree.delete(item)

    # Recalculate and update header
    remaining_events = []
    for item in tree.get_children():
        values = tree.item(item, 'values')
        dur_str = values[2]  # Duration is third column (index 2)
        if dur_str:
            # Parse duration back to seconds (approximate)
            remaining_events.append({'duration_seconds': _parse_duration(dur_str)})

    # Update would require access to header label - simpler to show confirmation
    messagebox.showinfo(
        "Deleted",
        f"Successfully deleted {deleted} {'entry' if deleted == 1 else 'entries'}.",
        parent=root
    )

    command_entry.delete(0, tk.END)
    return
```

**Step 2: Update command help text**

Update the unknown command message (around line 410-418) to include delete:

```python
messagebox.showwarning(
    "Unknown Command",
    f"Unknown command: '{command}'\n\n"
    f"Available commands:\n"
    f"  - delete - Delete selected entries\n"
    f"  - screenshots - Open main screenshots folder\n"
    f"  - periodic - Open periodic screenshots folder\n"
    f"  - actions - Open action screenshots folder\n"
    f"  - quit - Close application",
    parent=root
)
```

**Step 3: Test manually**

1. Run application
2. Open View Time window
3. Select one or more entries
4. Type 'delete' and press Enter
5. Confirm in dialog
6. Verify entries are removed from list

**Step 4: Commit**

```bash
git add src/SyncoPaid/__main__.py
git commit -m "feat: add delete command to View Time window

Allows deleting selected log entries:
- Select entries using click, Ctrl+click, or Shift+click
- Type 'delete' in command field
- Confirm deletion in dialog
- Entries removed from database and UI"
```

---

## Task 5: Update total activity time after deletion

**Files:**
- Modify: `src\SyncoPaid\__main__.py` (View Time window)

**Step 1: Extract header label to variable**

Change the header label creation (around line 352-356) from:

```python
tk.Label(
    header,
    text=f"Activity: {format_duration(total_seconds)} ({len(events)} events)",
    font=('Segoe UI', 12, 'bold')
).pack()
```

To:

```python
header_label = tk.Label(
    header,
    text=f"Activity: {format_duration(total_seconds)} ({len(events)} events)",
    font=('Segoe UI', 12, 'bold')
)
header_label.pack()
```

**Step 2: Create helper function to recalculate totals**

Add this function inside `run_window()`, before `execute_command()`:

```python
def update_header_totals():
    """Recalculate and update the header with current totals."""
    total_secs = 0
    count = 0
    for item in tree.get_children():
        values = tree.item(item, 'values')
        dur_str = values[2]  # Duration is third column (index 2)
        if dur_str:
            # Parse duration string back to seconds
            total_secs += _parse_duration_to_seconds(dur_str)
        count += 1
    header_label.config(
        text=f"Activity: {format_duration(total_secs)} ({count} events)"
    )
```

**Step 3: Add duration parsing helper**

Add this helper function at module level (after imports, around line 30):

```python
def _parse_duration_to_seconds(duration_str: str) -> float:
    """
    Parse a duration string like '2h 15m' or '45m' or '30s' back to seconds.

    Args:
        duration_str: Duration in format from format_duration()

    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0

    total = 0.0

    # Handle hours
    if 'h' in duration_str:
        parts = duration_str.split('h')
        total += int(parts[0].strip()) * 3600
        duration_str = parts[1] if len(parts) > 1 else ''

    # Handle minutes
    if 'm' in duration_str:
        parts = duration_str.split('m')
        total += int(parts[0].strip()) * 60
        duration_str = parts[1] if len(parts) > 1 else ''

    # Handle seconds
    if 's' in duration_str:
        parts = duration_str.split('s')
        total += int(parts[0].strip())

    return total
```

**Step 4: Call update after deletion**

In the delete command handler, replace the showinfo with:

```python
# Update header totals
update_header_totals()

messagebox.showinfo(
    "Deleted",
    f"Successfully deleted {deleted} {'entry' if deleted == 1 else 'entries'}.",
    parent=root
)
```

**Step 5: Test manually**

1. Open View Time window, note total time
2. Delete some entries
3. Verify total time in header decreases appropriately

**Step 6: Commit**

```bash
git add src/SyncoPaid/__main__.py
git commit -m "feat: update activity totals after deleting entries

Header now shows recalculated total time and event count
after entries are deleted."
```

---

## Task 6: Final integration test

**Test checklist:**

- [ ] Open View Time window - entries display correctly
- [ ] Select single entry - highlighted
- [ ] Ctrl+click to add to selection - multiple highlighted
- [ ] Shift+click to select range - range highlighted
- [ ] Type 'delete' with no selection - warning shown
- [ ] Type 'delete' with selection - confirmation dialog appears
- [ ] Cancel deletion - nothing deleted
- [ ] Confirm deletion - entries removed from list
- [ ] Header total updates after deletion
- [ ] Close and reopen View Time - deleted entries stay deleted
- [ ] Type 'help' or unknown command - shows available commands including 'delete'

**Final commit:**

```bash
git add -A
git commit -m "feat: complete delete log entries feature (story 1.1.4.3)

Adds ability to delete selected log entries from View Time window:
- Multi-select enabled (click, Ctrl+click, Shift+click)
- 'delete' command removes selected entries after confirmation
- Activity totals update after deletion
- Entries permanently removed from database

Acceptance criteria met:
- User can select one or more rows in Treeview
- Typing 'delete' deletes selected entries
- Confirmation dialog shown before deletion
- Events permanently removed from database
- Treeview refreshes after deletion
- Total activity time updates after deletion"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add `delete_events_by_ids()` | database.py |
| 2 | Store event IDs in Treeview | __main__.py |
| 3 | Enable multi-select | __main__.py |
| 4 | Add delete command handler | __main__.py |
| 5 | Update totals after deletion | __main__.py |
| 6 | Integration test | - |

**Estimated changes:** ~100 lines of code across 2 files
