"""Tests for screenshot archiver."""
import os
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
