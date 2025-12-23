"""Screenshot review dialog for discrete deletion of sensitive records."""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from syncopaid.database import Database


class ScreenshotReviewDialog:
    """
    Dialog for reviewing and deleting screenshots.

    Provides a list of captured screenshots with the ability to
    select and securely delete sensitive content.
    """

    def __init__(self, parent: tk.Tk, db: Database):
        """
        Initialize the screenshot review dialog.

        Args:
            parent: Parent tkinter window
            db: Database instance for screenshot operations
        """
        self.parent = parent
        self.db = db
        self.window: Optional[tk.Toplevel] = None
        self.screenshots = []

    def show(self):
        """Show the screenshot review dialog."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Review Screenshots")
        self.window.geometry("800x600")
        self.window.transient(self.parent)

        # Load screenshots from database
        self.screenshots = self.db.get_screenshots(limit=100)

        # Create main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Listbox for screenshots
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=20)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate listbox
        for screenshot in self.screenshots:
            display_text = f"{screenshot['captured_at'][:19]} - {screenshot.get('window_title', 'Unknown')}"
            self.listbox.insert(tk.END, display_text)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Delete Selected", command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def _delete_selected(self):
        """Delete selected screenshots."""
        pass  # Will implement in next task
