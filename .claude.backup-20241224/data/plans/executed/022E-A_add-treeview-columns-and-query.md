# 022E-A: Add Client/Matter Columns to Treeview and Update Query
Story ID: 8.1.2

## Task
Add Client and Matter columns to the main window treeview and update the event query to include these columns.

## Context
This is part A of the time assignment UI implementation. Before users can assign clients/matters to events, the treeview must display these columns.

## Scope
1. Add 'client' and 'matter' columns to the treeview definition
2. Update the event query to include client and matter fields

## Implementation Details

### Task 1: Add Columns to Treeview

In `src/syncopaid/main_ui_windows.py`, locate the treeview column definition (around line 227) and add:

```python
# Update columns tuple to include client and matter
columns = ('id', 'start', 'duration', 'end', 'app', 'title', 'client', 'matter')

# Add headings for new columns
tree.heading('client', text='Client')
tree.heading('matter', text='Matter')
tree.column('client', width=120, minwidth=80)
tree.column('matter', width=120, minwidth=80)
```

### Task 2: Update Event Query

Update the SELECT query that populates the treeview to include client and matter columns:

```python
cursor.execute(
    """SELECT id, timestamp, duration_seconds, end_time, app, title, client, matter
       FROM events
       WHERE timestamp >= ? AND is_idle = 0
       ORDER BY timestamp DESC""",
    (cutoff_iso,)
)
```

## Verification
```bash
venv\Scripts\activate
python -m syncopaid
```

1. Open main window
2. Verify Client and Matter columns appear in treeview
3. Verify existing events display (columns may be empty initially)

## Dependencies
- Tasks 022A-022D complete (schema has client/matter columns)

## Next Sub-Plan
022E-B adds the assignment dialog functionality.
