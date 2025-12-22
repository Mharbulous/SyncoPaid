"""Tests for screenshot archiver."""
import os
import zipfile
from datetime import datetime
from pathlib import Path
import pytest
from syncopaid.archiver import ArchiveWorker


def test_detect_archivable_months(tmp_path):
    """Test identifies folders eligible for archiving (one clear month passed)."""
    # Setup test structure
    screenshot_dir = tmp_path / "screenshots"
    archive_dir = tmp_path / "archives"
    screenshot_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    # Create test folders
    (screenshot_dir / "2025-09-15").mkdir()
    (screenshot_dir / "2025-10-20").mkdir()
    (screenshot_dir / "2025-11-05").mkdir()

    # Given: today is 2025-12-16, folders: 2025-09-15, 2025-10-20, 2025-11-05
    # When: checking archivable folders
    # Then: only 2025-09-* and 2025-10-* are archivable (Nov is not complete)
    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    folders = archiver.get_archivable_folders(reference_date=datetime(2025, 12, 16))
    assert "2025-09-15" in folders
    assert "2025-10-20" in folders
    assert "2025-11-05" not in folders


def test_group_folders_by_month():
    """Test groups folders by YYYY-MM for zip creation."""
    folders = ["2025-10-01", "2025-10-15", "2025-10-31", "2025-09-20"]
    grouped = ArchiveWorker.group_by_month(folders)
    assert grouped == {
        "2025-10": ["2025-10-01", "2025-10-15", "2025-10-31"],
        "2025-09": ["2025-09-20"]
    }


def test_create_archive(tmp_path):
    """Test creates zip file with correct naming and contents."""
    # Setup test folders with screenshots
    screenshot_dir = tmp_path / "screenshots"
    (screenshot_dir / "2025-10-01").mkdir(parents=True)
    (screenshot_dir / "2025-10-15").mkdir(parents=True)
    (screenshot_dir / "2025-10-01" / "test1.jpg").write_text("img1")
    (screenshot_dir / "2025-10-15" / "test2.jpg").write_text("img2")

    archive_dir = tmp_path / "archives"
    archiver = ArchiveWorker(screenshot_dir, archive_dir)

    zip_path = archiver.create_archive("2025-10", ["2025-10-01", "2025-10-15"])

    assert zip_path.exists()
    assert zip_path.name == "2025-10_screenshots.zip"
    # Verify zip contents
    with zipfile.ZipFile(zip_path) as zf:
        assert "2025-10-01/test1.jpg" in zf.namelist()
        assert "2025-10-15/test2.jpg" in zf.namelist()


def test_cleanup_after_archive(tmp_path):
    screenshot_dir = tmp_path / "screenshots"
    (screenshot_dir / "2025-10-01").mkdir(parents=True)
    (screenshot_dir / "2025-10-01" / "test.jpg").write_text("img")

    archive_dir = tmp_path / "archives"
    archiver = ArchiveWorker(screenshot_dir, archive_dir)

    archiver.archive_month("2025-10", ["2025-10-01"])

    assert not (screenshot_dir / "2025-10-01").exists()
    assert (archive_dir / "2025-10_screenshots.zip").exists()


def test_archive_worker_startup(tmp_path, mocker):
    """Test archiver runs on startup and schedules monthly checks."""
    screenshot_dir = tmp_path / "screenshots"
    (screenshot_dir / "2025-10-01").mkdir(parents=True)
    (screenshot_dir / "2025-10-01" / "test.jpg").write_text("img")

    archive_dir = tmp_path / "archives"
    archiver = ArchiveWorker(screenshot_dir, archive_dir)

    # Mock archive_month to verify it's called
    mock_archive_month = mocker.patch.object(archiver, 'archive_month')

    archiver.run_once()  # Synchronous run for testing

    # Verify archivable months were processed
    assert mock_archive_month.called


def test_error_dialog(tmp_path, mocker):
    """Test error handler shows tkinter dialog with retry options."""
    import sys
    from unittest.mock import patch, MagicMock

    screenshot_dir = tmp_path / "screenshots"
    archive_dir = tmp_path / "archives"

    # Create mock tkinter modules
    mock_root = MagicMock()
    mock_tk = MagicMock()
    mock_tk.Tk.return_value = mock_root

    mock_messagebox = MagicMock()
    mock_messagebox.askretrycancel.return_value = True  # Retry now

    # Set up messagebox as an attribute of mock_tk
    mock_tk.messagebox = mock_messagebox

    # Inject mocks into sys.modules before import
    with patch.dict(sys.modules, {
        'tkinter': mock_tk,
        'tkinter.messagebox': mock_messagebox
    }):
        archiver = ArchiveWorker(screenshot_dir, archive_dir)
        archiver._handle_error("2025-10", Exception("Disk full"))

    assert mock_messagebox.askretrycancel.called
    assert mock_root.withdraw.called
    assert mock_root.destroy.called
