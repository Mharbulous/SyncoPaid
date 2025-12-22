"""
Tests for client_matter_importer module.

Tests folder parsing for Client > Matter hierarchy.
"""
import pytest
from pathlib import Path
from syncopaid.client_matter_importer import (
    ImportedClient,
    ImportedMatter,
    ImportResult,
    import_from_folder,
    EXCLUDED_FOLDERS
)


class TestDataClasses:
    """Test data classes structure."""

    def test_imported_client_structure(self):
        """ImportedClient should have display_name and folder_path."""
        client = ImportedClient(
            display_name="Smith, John",
            folder_path="/tmp/clients/Smith, John"
        )
        assert client.display_name == "Smith, John"
        assert client.folder_path == "/tmp/clients/Smith, John"

    def test_imported_matter_structure(self):
        """ImportedMatter should have client_display_name, display_name, and folder_path."""
        matter = ImportedMatter(
            client_display_name="Smith, John",
            display_name="Estate Planning 2024",
            folder_path="/tmp/clients/Smith, John/Estate Planning 2024"
        )
        assert matter.client_display_name == "Smith, John"
        assert matter.display_name == "Estate Planning 2024"
        assert matter.folder_path == "/tmp/clients/Smith, John/Estate Planning 2024"

    def test_import_result_structure(self):
        """ImportResult should have clients, matters, root_path, and stats."""
        result = ImportResult(
            clients=[],
            matters=[],
            root_path="/tmp/clients",
            stats={"clients": 0, "matters": 0}
        )
        assert result.clients == []
        assert result.matters == []
        assert result.root_path == "/tmp/clients"
        assert result.stats == {"clients": 0, "matters": 0}


class TestEmptyFolder:
    """Test handling of empty folders."""

    def test_empty_folder_returns_empty_lists(self, tmp_path):
        """Empty folder should return empty clients and matters lists."""
        result = import_from_folder(str(tmp_path))

        assert result.clients == []
        assert result.matters == []
        assert result.root_path == str(tmp_path)
        assert result.stats == {"clients": 0, "matters": 0}


class TestClientMatterHierarchy:
    """Test parsing Client > Matter folder hierarchy."""

    def test_single_client_no_matters(self, tmp_path):
        """Client folder with no subfolders should create client only."""
        client_dir = tmp_path / "ClientA"
        client_dir.mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.clients) == 1
        assert result.clients[0].display_name == "ClientA"
        assert result.clients[0].folder_path == str(client_dir)
        assert len(result.matters) == 0
        assert result.stats == {"clients": 1, "matters": 0}

    def test_client_with_matters(self, tmp_path):
        """Client folder with matter subfolders should create both."""
        client_dir = tmp_path / "ClientA"
        client_dir.mkdir()
        matter1 = client_dir / "Matter1"
        matter1.mkdir()
        matter2 = client_dir / "Matter2"
        matter2.mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.clients) == 1
        assert result.clients[0].display_name == "ClientA"

        assert len(result.matters) == 2
        assert result.matters[0].client_display_name == "ClientA"
        assert result.matters[0].display_name == "Matter1"
        assert result.matters[0].folder_path == str(matter1)
        assert result.matters[1].client_display_name == "ClientA"
        assert result.matters[1].display_name == "Matter2"
        assert result.matters[1].folder_path == str(matter2)

        assert result.stats == {"clients": 1, "matters": 2}

    def test_multiple_clients_with_matters(self, tmp_path):
        """Multiple clients each with matters."""
        client_a = tmp_path / "ClientA"
        client_a.mkdir()
        (client_a / "Matter1").mkdir()
        (client_a / "Matter2").mkdir()

        client_b = tmp_path / "ClientB"
        client_b.mkdir()
        (client_b / "MatterX").mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.clients) == 2
        assert result.clients[0].display_name == "ClientA"
        assert result.clients[1].display_name == "ClientB"

        assert len(result.matters) == 3
        assert result.stats == {"clients": 2, "matters": 3}


class TestExcludedFolders:
    """Test filtering of system and hidden folders."""

    def test_hidden_folders_excluded(self, tmp_path):
        """Folders starting with . should be excluded."""
        (tmp_path / ".git").mkdir()
        (tmp_path / ".vscode").mkdir()
        (tmp_path / "ValidClient").mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.clients) == 1
        assert result.clients[0].display_name == "ValidClient"

    def test_system_folders_excluded(self, tmp_path):
        """System folders should be excluded."""
        (tmp_path / "$RECYCLE.BIN").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "ValidClient").mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.clients) == 1
        assert result.clients[0].display_name == "ValidClient"

    def test_files_ignored(self, tmp_path):
        """Files at root level should be ignored."""
        (tmp_path / "readme.txt").touch()
        (tmp_path / "ValidClient").mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.clients) == 1
        assert result.clients[0].display_name == "ValidClient"

    def test_excluded_matter_folders(self, tmp_path):
        """Excluded folders within client folders should be skipped."""
        client_dir = tmp_path / "ClientA"
        client_dir.mkdir()
        (client_dir / ".git").mkdir()
        (client_dir / "ValidMatter").mkdir()

        result = import_from_folder(str(tmp_path))

        assert len(result.matters) == 1
        assert result.matters[0].display_name == "ValidMatter"


class TestSorting:
    """Test that results are sorted alphabetically."""

    def test_clients_sorted_alphabetically(self, tmp_path):
        """Clients should be sorted by name."""
        (tmp_path / "Zebra").mkdir()
        (tmp_path / "Alpha").mkdir()
        (tmp_path / "Beta").mkdir()

        result = import_from_folder(str(tmp_path))

        assert result.clients[0].display_name == "Alpha"
        assert result.clients[1].display_name == "Beta"
        assert result.clients[2].display_name == "Zebra"

    def test_matters_sorted_alphabetically(self, tmp_path):
        """Matters should be sorted by name within each client."""
        client_dir = tmp_path / "ClientA"
        client_dir.mkdir()
        (client_dir / "Zebra").mkdir()
        (client_dir / "Alpha").mkdir()
        (client_dir / "Beta").mkdir()

        result = import_from_folder(str(tmp_path))

        assert result.matters[0].display_name == "Alpha"
        assert result.matters[1].display_name == "Beta"
        assert result.matters[2].display_name == "Zebra"
