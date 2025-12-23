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
