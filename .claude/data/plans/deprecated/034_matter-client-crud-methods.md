# 034: Matter/Client Database - CRUD Methods

## Task
Add Database methods for creating, reading, updating, and deleting clients and matters.

## Context
Extends the Database class with methods to manage client and matter records. Uses existing patterns from insert_event() and get_events().

## Scope
- Client methods: insert_client, get_clients, update_client, delete_client
- Matter methods: insert_matter, get_matters, update_matter, update_matter_status

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database.py` | Add CRUD methods |
| `tests/test_matter_client.py` | Add CRUD tests |

## Implementation

### Client CRUD Tests

```python
# tests/test_matter_client.py (add)
def test_client_crud_operations():
    """Test create, read, update, delete operations for clients."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Create
        client_id = db.insert_client(name="Acme Corp", notes="Tech startup")
        assert client_id > 0

        # Read
        clients = db.get_clients()
        assert len(clients) == 1
        assert clients[0]['name'] == "Acme Corp"

        # Update
        db.update_client(client_id, name="Acme Corporation", notes="Updated")
        clients = db.get_clients()
        assert clients[0]['name'] == "Acme Corporation"

        # Delete
        db.delete_client(client_id)
        assert len(db.get_clients()) == 0
```

### Client CRUD Methods

```python
# src/syncopaid/database.py (add after existing methods)
def insert_client(self, name: str, notes: Optional[str] = None) -> int:
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clients (name, notes) VALUES (?, ?)", (name, notes))
        return cursor.lastrowid

def get_clients(self) -> List[Dict]:
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]

def update_client(self, client_id: int, name: str, notes: Optional[str] = None):
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE clients SET name = ?, notes = ? WHERE id = ?",
                      (name, notes, client_id))

def delete_client(self, client_id: int):
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
```

### Matter CRUD Tests

```python
# tests/test_matter_client.py (add)
def test_matter_crud_operations():
    """Test matter CRUD with status filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")
        assert matter_id > 0

        # Read active
        matters = db.get_matters()
        assert len(matters) == 1
        assert matters[0]['status'] == 'active'

        # Archive
        db.update_matter_status(matter_id, 'archived')
        assert len(db.get_matters(status='active')) == 0
        assert len(db.get_matters(status='all')) == 1
```

### Matter CRUD Methods

```python
# src/syncopaid/database.py (add)
def insert_matter(self, matter_number: str, client_id: Optional[int] = None,
                  description: Optional[str] = None, status: str = 'active') -> int:
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO matters (matter_number, client_id, description, status)
            VALUES (?, ?, ?, ?)
        """, (matter_number, client_id, description, status))
        return cursor.lastrowid

def get_matters(self, status: str = 'active') -> List[Dict]:
    with self._get_connection() as conn:
        cursor = conn.cursor()
        if status == 'all':
            cursor.execute("""
                SELECT m.*, c.name as client_name FROM matters m
                LEFT JOIN clients c ON m.client_id = c.id
                ORDER BY m.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT m.*, c.name as client_name FROM matters m
                LEFT JOIN clients c ON m.client_id = c.id
                WHERE m.status = ? ORDER BY m.created_at DESC
            """, (status,))
        return [dict(row) for row in cursor.fetchall()]

def update_matter(self, matter_id: int, matter_number: str,
                  client_id: Optional[int] = None, description: Optional[str] = None):
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE matters SET matter_number = ?, client_id = ?, description = ?,
            updated_at = datetime('now') WHERE id = ?
        """, (matter_number, client_id, description, matter_id))

def update_matter_status(self, matter_id: int, status: str):
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE matters SET status = ?, updated_at = datetime('now') WHERE id = ?
        """, (status, matter_id))
```

## Verification

```bash
venv\Scripts\activate
python tests/test_matter_client.py
```

## Dependencies
- Task 033 (schema tables)

## Next Task
After this: `035_matter-client-client-dialog.md`
