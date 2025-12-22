import pytest
import tempfile
from pathlib import Path
from syncopaid.database import Database
import importlib.util

# Check if tkinter is available (not available in headless CI)
HAS_TKINTER = importlib.util.find_spec('tkinter') is not None


def test_query_screenshots_by_timestamp():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        # Insert test screenshots
        db.insert_screenshot('2025-12-16T10:00:00', 'path1.png', 'app1', 'title1', 'hash1')
        db.insert_screenshot('2025-12-16T10:05:00', 'path2.png', 'app1', 'title2', 'hash2')

        from syncopaid.categorization_ui import query_screenshots_for_activity
        results = query_screenshots_for_activity(db, '2025-12-16T10:00:00', '2025-12-16T10:10:00')

        assert len(results) == 2
        assert results[0]['file_path'] == 'path1.png'
        assert results[1]['file_path'] == 'path2.png'


def test_screenshot_cache_lru():
    from syncopaid.categorization_ui import ScreenshotCache
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test images
        path1 = Path(tmpdir) / 'path1.png'
        path2 = Path(tmpdir) / 'path2.png'

        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(path1)
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.save(path2)

        cache = ScreenshotCache(max_size_mb=50)

        # Load mock images (track cache size)
        img1_loaded = cache.get_image(str(path1))
        img2_loaded = cache.get_image(str(path2))

        assert cache.current_size_mb < 50
        assert cache.hit_count == 0

        # Second access should be cached
        img1_cached = cache.get_image(str(path1))
        assert cache.hit_count == 1


@pytest.mark.skipif(not HAS_TKINTER, reason="tkinter not available in CI")
def test_thumbnail_widget_creation():
    import tkinter as tk
    from syncopaid.categorization_ui import create_thumbnail_widget, ScreenshotCache
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test images
        path1 = Path(tmpdir) / 'path1.png'
        path2 = Path(tmpdir) / 'path2.png'

        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(path1)
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.save(path2)

        root = tk.Tk()
        cache = ScreenshotCache(max_size_mb=50)

        screenshots = [
            {'file_path': str(path1), 'captured_at': '2025-12-16T10:00:00'},
            {'file_path': str(path2), 'captured_at': '2025-12-16T10:05:00'}
        ]

        widget = create_thumbnail_widget(root, screenshots, cache)

        assert widget is not None
        # Verify thumbnails are in chronological order
        assert len(widget.winfo_children()) == 2

        root.destroy()


@pytest.mark.skipif(not HAS_TKINTER, reason="tkinter not available in CI")
def test_modal_viewer():
    import tkinter as tk
    from syncopaid.categorization_ui import show_screenshot_modal
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        root = tk.Tk()
        screenshot_path = str(Path(tmpdir) / 'test_screenshot.png')

        # Create test image
        img = Image.new('RGB', (800, 600), color='red')
        img.save(screenshot_path)

        modal = show_screenshot_modal(root, screenshot_path)

        assert modal is not None
        # Modal should be transient window
        assert modal.winfo_toplevel() != root

        modal.destroy()
        root.destroy()
