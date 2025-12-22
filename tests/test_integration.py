"""Integration tests for SyncoPaid app."""
import pytest
from pathlib import Path


def test_app_initializes_archiver(tmp_path):
    """Test app initializes archiver on startup."""
    # Verify archiver integration by reading the source code
    # This is a static test to verify the integration exists

    main_app_file = Path(__file__).parent.parent / "src" / "syncopaid" / "main_app_class.py"
    content = main_app_file.read_text()

    # Verify ArchiveWorker is imported
    assert "from syncopaid.archiver import ArchiveWorker" in content, \
        "ArchiveWorker not imported in main_app_class.py"

    # Verify archiver is instantiated
    assert "self.archiver = ArchiveWorker(" in content, \
        "ArchiveWorker not instantiated in __init__"

    # Verify run_once is called
    assert "self.archiver.run_once()" in content, \
        "archiver.run_once() not called on startup"

    # Verify start_background is called
    assert "self.archiver.start_background()" in content, \
        "archiver.start_background() not called"

    # Verify archiver has required methods (test the archiver module directly)
    from syncopaid.archiver import ArchiveWorker
    test_screenshot_dir = tmp_path / "screenshots"
    test_archive_dir = tmp_path / "archives"
    test_screenshot_dir.mkdir(parents=True)

    archiver = ArchiveWorker(test_screenshot_dir, test_archive_dir)
    assert hasattr(archiver, 'run_once')
    assert hasattr(archiver, 'start_background')
    assert callable(archiver.run_once)
    assert callable(archiver.start_background)
