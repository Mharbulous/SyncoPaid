"""Test matter and client database functionality."""
import sqlite3
import tempfile
from pathlib import Path
from syncopaid.database import Database

def test_clients_table_exists():
    """Verify clients table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "clients table should exist"

def test_matters_table_exists():
    """Verify matters table is created with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matters'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "matters table should exist"

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

def test_client_dialog_module_exists():
    from syncopaid.matter_client_dialog import ClientDialog
    assert callable(ClientDialog)

if __name__ == "__main__":
    test_clients_table_exists()
    test_matters_table_exists()
    test_client_crud_operations()
    test_matter_crud_operations()
    test_client_dialog_module_exists()
    print("All tests passed!")
