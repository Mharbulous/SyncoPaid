"""
Screenshot-assisted time categorization UI components.

Provides UI components for displaying screenshots during the categorization
flow when AI confidence is low.
"""

from typing import List, Dict
from PIL import Image, ImageTk
import os
import importlib.util

# Check if tkinter is available
HAS_TKINTER = importlib.util.find_spec('tkinter') is not None

if HAS_TKINTER:
    import tkinter as tk
    from tkinter import ttk


def query_screenshots_for_activity(db, start_time: str, end_time: str) -> List[Dict]:
    """Query screenshots within activity timestamp range."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, captured_at, file_path, window_app, window_title
            FROM screenshots
            WHERE captured_at >= ? AND captured_at <= ?
            ORDER BY captured_at ASC
        """, (start_time, end_time))
        return [dict(row) for row in cursor.fetchall()]


class ScreenshotCache:
    def __init__(self, max_size_mb: int = 50):
        self.max_size_mb = max_size_mb
        self.cache = {}
        self.current_size_mb = 0
        self.hit_count = 0

    def get_image(self, path: str):
        if path in self.cache:
            self.hit_count += 1
            return self.cache[path]

        if os.path.exists(path):
            img = Image.open(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)

            # Evict if needed
            while self.current_size_mb + size_mb > self.max_size_mb and self.cache:
                oldest_key = next(iter(self.cache))
                self._evict(oldest_key)

            self.cache[path] = img
            self.current_size_mb += size_mb
            return img
        return None

    def _evict(self, key):
        if key in self.cache:
            size_mb = os.path.getsize(key) / (1024 * 1024)
            del self.cache[key]
            self.current_size_mb -= size_mb


def create_thumbnail_widget(parent, screenshots: List[Dict], cache: 'ScreenshotCache'):
    """Create scrollable thumbnail widget showing screenshots chronologically."""
    if not HAS_TKINTER:
        raise ImportError("tkinter is required for GUI components")

    frame = ttk.Frame(parent)

    # Create scrollable canvas
    canvas = tk.Canvas(frame, height=150)
    scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=scrollbar.set)

    inner_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # Add thumbnails
    for i, screenshot in enumerate(screenshots):
        img = cache.get_image(screenshot['file_path'])
        if img:
            thumb = img.copy()
            thumb.thumbnail((120, 90))
            photo = ImageTk.PhotoImage(thumb)

            btn = tk.Button(inner_frame, image=photo)
            btn.image = photo  # Keep reference
            btn.grid(row=0, column=i, padx=5)

            # Add timestamp label
            label = tk.Label(inner_frame, text=screenshot['captured_at'][11:19])
            label.grid(row=1, column=i)

    canvas.pack(side="top", fill="both", expand=True)
    scrollbar.pack(side="bottom", fill="x")

    return frame
