# 052: LLM & AI Integration - Review UI

## Task
Create a review UI for approving/editing AI-generated billing entries.

## Context
Users need to review AI-generated narratives and matter assignments before exporting for billing. This provides a simple tkinter dialog for batch review.

## Scope
- Create ReviewUI class in a new module
- Load entries for review
- Approve/Edit/Skip workflow
- Persist changes to database

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/review_ui.py` | New module (CREATE) |
| `tests/test_review_ui.py` | Create test file |

## Implementation

```python
# src/syncopaid/review_ui.py (CREATE)
"""Review UI for AI-generated billing entries."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List, Callable
from .database import Database


class ReviewEntry:
    """A billing entry pending review."""

    def __init__(self, event_id: int, matter: str, narrative: str, time_hours: float):
        self.event_id = event_id
        self.matter = matter
        self.narrative = narrative
        self.time_hours = time_hours
        self.status: Optional[str] = None  # 'approved', 'edited', 'skipped'


class ReviewUI:
    """
    Dialog for reviewing and approving AI-generated billing entries.

    Provides approve/edit/skip workflow for batch processing.
    """

    def __init__(self, parent=None, db: Optional[Database] = None):
        """
        Initialize review UI.

        Args:
            parent: Optional parent tkinter window
            db: Optional database for persisting changes
        """
        self.db = db
        self.current_entry: Optional[ReviewEntry] = None
        self.status: Optional[str] = None
        self.entries: List[ReviewEntry] = []
        self.current_index = 0

        if parent:
            self._create_window(parent)

    def _create_window(self, parent):
        """Create the review dialog window."""
        self.window = tk.Toplevel(parent)
        self.window.title("Review AI-Generated Entries")
        self.window.geometry("700x400")

        # Entry display
        display_frame = ttk.Frame(self.window, padding=20)
        display_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(display_frame, text="Matter:").grid(row=0, column=0, sticky=tk.W)
        self.matter_var = tk.StringVar()
        ttk.Entry(display_frame, textvariable=self.matter_var, width=50).grid(row=0, column=1, pady=5)

        ttk.Label(display_frame, text="Time:").grid(row=1, column=0, sticky=tk.W)
        self.time_var = tk.StringVar()
        ttk.Entry(display_frame, textvariable=self.time_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(display_frame, text="Narrative:").grid(row=2, column=0, sticky=tk.NW)
        self.narrative_text = tk.Text(display_frame, height=6, width=60)
        self.narrative_text.grid(row=2, column=1, pady=5)

        # Progress
        self.progress_var = tk.StringVar(value="Entry 0 of 0")
        ttk.Label(display_frame, textvariable=self.progress_var).grid(row=3, column=1, pady=10)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Approve", command=self.approve).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit & Approve", command=self.edit_and_approve).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skip", command=self.skip).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        self.window.transient(parent)
        self.window.grab_set()

    def load_entries(self, entries: List[ReviewEntry]):
        """Load entries for review."""
        self.entries = entries
        self.current_index = 0
        if entries:
            self._display_current()

    def load_entry(self, entry: ReviewEntry):
        """Load a single entry for review (legacy API)."""
        self.current_entry = entry
        if hasattr(self, 'matter_var'):
            self.matter_var.set(entry.matter or '')
            self.time_var.set(f"{entry.time_hours:.1f}")
            self.narrative_text.delete('1.0', tk.END)
            self.narrative_text.insert('1.0', entry.narrative or '')

    def _display_current(self):
        """Display the current entry in the UI."""
        if 0 <= self.current_index < len(self.entries):
            entry = self.entries[self.current_index]
            self.load_entry(entry)
            self.progress_var.set(f"Entry {self.current_index + 1} of {len(self.entries)}")

    def approve(self):
        """Approve current entry and move to next."""
        if self.current_entry:
            self.current_entry.status = 'approved'
            self.status = 'approved'
        self._next_entry()

    def edit_and_approve(self):
        """Save edits, approve, and move to next."""
        if self.current_entry:
            self.current_entry.matter = self.matter_var.get()
            self.current_entry.narrative = self.narrative_text.get('1.0', tk.END).strip()
            self.current_entry.status = 'edited'
            self.status = 'edited'
        self._next_entry()

    def skip(self):
        """Skip current entry and move to next."""
        if self.current_entry:
            self.current_entry.status = 'skipped'
            self.status = 'skipped'
        self._next_entry()

    def _next_entry(self):
        """Move to next entry or close if done."""
        self.current_index += 1
        if self.current_index < len(self.entries):
            self._display_current()
        else:
            messagebox.showinfo("Complete", f"Reviewed {len(self.entries)} entries.")
            if hasattr(self, 'window'):
                self.window.destroy()

    def get_status(self) -> Optional[str]:
        """Get the status of the current entry."""
        return self.status

    def get_approved_entries(self) -> List[ReviewEntry]:
        """Get all approved/edited entries."""
        return [e for e in self.entries if e.status in ('approved', 'edited')]
```

### Tests

```python
# tests/test_review_ui.py (CREATE)
"""Tests for review UI."""
import pytest
from syncopaid.review_ui import ReviewUI, ReviewEntry


def test_review_entry_creation():
    entry = ReviewEntry(
        event_id=1,
        matter='Matter 123',
        narrative='Research',
        time_hours=0.2
    )
    assert entry.event_id == 1
    assert entry.matter == 'Matter 123'
    assert entry.status is None


def test_review_ui_initialization():
    ui = ReviewUI()
    assert ui.current_entry is None
    assert ui.status is None


def test_review_entry_approval():
    ui = ReviewUI()
    entry = ReviewEntry(1, 'Matter 123', 'Research', 0.2)
    ui.load_entry(entry)
    ui.approve()
    assert ui.get_status() == 'approved'


def test_review_load_entries():
    ui = ReviewUI()
    entries = [
        ReviewEntry(1, 'M1', 'Work 1', 0.1),
        ReviewEntry(2, 'M2', 'Work 2', 0.2),
    ]
    ui.load_entries(entries)
    assert len(ui.entries) == 2
```

## Verification

```bash
pytest tests/test_review_ui.py -v
python -c "from syncopaid.review_ui import ReviewUI; print('OK')"
```

## Dependencies
- Task 051 (narrative generation)

## Next Task
After this: `053_llm-config-defaults.md`
