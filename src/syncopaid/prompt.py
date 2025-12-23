"""
Transition prompt dialog for asking users if now is a good time to categorize.

Uses tkinter for cross-platform GUI dialog.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class TransitionPrompt:
    """Prompt dialog asking user if now is a good time to categorize."""

    RESPONSES = {
        "free": "Yes, I'm free",
        "break": "No, I'm on break.",
        "interrupting": "No, I'm working.",
        "dismiss": "Not now, ask later."
    }

    def __init__(self):
        self.response: Optional[str] = None
        self.root: Optional[tk.Tk] = None

    def show(self, transition_type: str = None) -> Optional[str]:
        """
        Show prompt dialog and return user's response.

        Args:
            transition_type: Type of transition detected (for context)

        Returns:
            Response key ("free", "break", "interrupting", "dismiss") or None if dismissed
        """
        self.root = tk.Tk()
        self.root.title("SyncoPaid - Time Categorization")
        self.root.attributes('-topmost', True)

        # Set minimum width, let height auto-size to fit content
        self.root.minsize(400, 0)
        # Prevent horizontal resizing but allow vertical auto-sizing
        self.root.resizable(False, False)

        # Message
        msg = "Is now a good time to categorize your time?"
        if transition_type:
            msg += f"\n\n(Detected: {transition_type.replace('_', ' ').title()})"

        label = tk.Label(self.root, text=msg, font=('Segoe UI', 10), pady=20)
        label.pack()

        # Response buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=(10, 20))  # Extra bottom padding for last button

        for key, text in self.RESPONSES.items():
            btn = tk.Button(
                btn_frame,
                text=text,
                command=lambda k=key: self._handle_response(k),
                width=20
            )
            btn.pack(pady=5)

        self.root.mainloop()
        return self.response

    def _handle_response(self, response_key: str):
        """Handle button click."""
        self.response = response_key
        self.root.destroy()
