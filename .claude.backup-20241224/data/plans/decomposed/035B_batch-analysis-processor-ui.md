# Batch Analysis Processor & UI - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.3 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 035_batch-processing-on-demand.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add progress-aware batch processing to NightProcessor and create the BatchAnalysisDialog UI.

**Approach:** Extend NightProcessor with progress callbacks and cancellation, create tkinter dialog with progress bar.

**Tech Stack:** Python 3.11+, tkinter for UI, threading for background processing

---

## Story Context

**Title:** Batch Processing On-Demand (Part 2 of 3)
**Description:** Processing layer - NightProcessor extension and UI dialog

**Acceptance Criteria:**
- [ ] NightProcessor supports progress callbacks
- [ ] NightProcessor respects cancellation token
- [ ] Dialog shows progress bar and status text
- [ ] Dialog has cancel button that stops processing

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Sub-plan 035A completed (BatchAnalysisProgress dataclass exists)

## TDD Tasks

### Task 1: Add process_batch_with_progress to NightProcessor (~5 min)

**Files:**
- Modify: `src/syncopaid/night_processor.py`
- Test: `tests/test_night_processor.py`

**Context:** Extend NightProcessor with a method that supports progress tracking and cancellation. This wraps the existing processing logic with progress callbacks.

**Step 1 - RED:** Write failing test
```python
# tests/test_night_processor.py - add test
from syncopaid.batch_analysis_progress import BatchAnalysisProgress


def test_process_batch_with_progress_reports_progress():
    """Test that process_batch_with_progress calls progress callback."""
    progress_updates = []

    def mock_process_batch(batch_size: int) -> int:
        return 5  # Simulate processing 5 items

    def mock_get_pending_count() -> int:
        return 10

    processor = NightProcessor(
        get_pending_count=mock_get_pending_count,
        process_batch=mock_process_batch,
        batch_size=5
    )

    progress = BatchAnalysisProgress(
        total=10,
        on_progress=lambda p: progress_updates.append(p.processed)
    )

    processor.process_batch_with_progress(progress)

    assert len(progress_updates) > 0
    assert progress.is_complete is True


def test_process_batch_with_progress_respects_cancellation():
    """Test that cancellation stops processing."""
    process_count = [0]

    def mock_process_batch(batch_size: int) -> int:
        process_count[0] += 1
        return batch_size

    def mock_get_pending_count() -> int:
        return 100  # Many items

    processor = NightProcessor(
        get_pending_count=mock_get_pending_count,
        process_batch=mock_process_batch,
        batch_size=5
    )

    progress = BatchAnalysisProgress(total=100)
    progress.cancel()  # Cancel immediately

    processor.process_batch_with_progress(progress)

    assert process_count[0] == 0  # Should not process anything
    assert progress.is_complete is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_night_processor.py::test_process_batch_with_progress_reports_progress -v
```
Expected output: `FAILED` (AttributeError: 'NightProcessor' object has no attribute 'process_batch_with_progress')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/night_processor.py - add import at top
from syncopaid.batch_analysis_progress import BatchAnalysisProgress

# Add method to NightProcessor class (after trigger_manual method)
def process_batch_with_progress(self, progress: BatchAnalysisProgress) -> int:
    """
    Process screenshots with progress tracking and cancellation support.

    Args:
        progress: BatchAnalysisProgress instance for tracking

    Returns:
        Total number of screenshots processed
    """
    if self._process_batch is None:
        progress.is_complete = True
        return 0

    total_processed = 0

    while not progress.is_cancelled:
        if self._get_pending_count is None:
            break

        pending = self._get_pending_count()
        if pending == 0:
            break

        batch_processed = self._process_batch(self.batch_size)
        total_processed += batch_processed
        progress.update(processed=total_processed)

        if batch_processed == 0:
            break

    progress.is_complete = True
    progress.update()  # Final update
    return total_processed
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_night_processor.py::test_process_batch_with_progress_reports_progress -v
pytest tests/test_night_processor.py::test_process_batch_with_progress_respects_cancellation -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/night_processor.py tests/test_night_processor.py && git commit -m "feat(8.6.3): add process_batch_with_progress with cancellation support"
```

---

### Task 2: Create BatchAnalysisDialog UI (~8 min)

**Files:**
- Create: `src/syncopaid/batch_analysis_dialog.py`
- Test: `tests/test_batch_analysis_dialog.py`

**Context:** A tkinter dialog that shows processing progress with a progress bar, status text, and cancel button. This dialog runs the analysis in a background thread to keep UI responsive.

**Step 1 - RED:** Write failing test
```python
# tests/test_batch_analysis_dialog.py
import pytest
from unittest.mock import MagicMock, patch


def test_batch_analysis_dialog_initialization():
    """Test dialog initializes without errors."""
    with patch('syncopaid.batch_analysis_dialog.tk.Toplevel'):
        from syncopaid.batch_analysis_dialog import BatchAnalysisDialog

        mock_processor = MagicMock()
        mock_processor.batch_size = 10

        mock_get_pending = MagicMock(return_value=50)

        dialog = BatchAnalysisDialog(
            parent=None,
            night_processor=mock_processor,
            get_pending_count=mock_get_pending
        )

        assert dialog.total_pending == 50


def test_batch_analysis_dialog_cancel_sets_flag():
    """Test cancel button sets cancellation flag."""
    with patch('syncopaid.batch_analysis_dialog.tk.Toplevel'):
        from syncopaid.batch_analysis_dialog import BatchAnalysisDialog

        mock_processor = MagicMock()
        mock_get_pending = MagicMock(return_value=10)

        dialog = BatchAnalysisDialog(
            parent=None,
            night_processor=mock_processor,
            get_pending_count=mock_get_pending
        )

        dialog._on_cancel()

        assert dialog.progress.is_cancelled is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_batch_analysis_dialog.py -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.batch_analysis_dialog')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/batch_analysis_dialog.py
"""Batch analysis progress dialog."""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import Callable, Optional

from syncopaid.batch_analysis_progress import BatchAnalysisProgress


class BatchAnalysisDialog:
    """
    Dialog showing batch screenshot analysis progress.

    Features:
    - Progress bar with percentage
    - Status text (X of Y processed)
    - Cancel button
    - Performance warning before starting
    - Runs analysis in background thread
    """

    def __init__(
        self,
        parent: Optional[tk.Tk],
        night_processor,
        get_pending_count: Callable[[], int]
    ):
        """
        Initialize batch analysis dialog.

        Args:
            parent: Parent tkinter window (or None for standalone)
            night_processor: NightProcessor instance with process_batch_with_progress
            get_pending_count: Function returning count of pending screenshots
        """
        self.night_processor = night_processor
        self.get_pending_count = get_pending_count
        self.total_pending = get_pending_count()

        self.progress = BatchAnalysisProgress(
            total=self.total_pending,
            on_progress=self._update_ui
        )

        self._processing_thread: Optional[threading.Thread] = None
        self._create_window(parent)

    def _create_window(self, parent: Optional[tk.Tk]):
        """Create the dialog window."""
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("Analyze Screenshots")
        self.window.geometry("400x180")
        self.window.resizable(False, False)

        # Main frame with padding
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_var = tk.StringVar(value=f"Ready to analyze {self.total_pending} screenshots")
        ttk.Label(frame, textvariable=self.status_var).pack(pady=(0, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            frame,
            orient=tk.HORIZONTAL,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)

        # Percentage label
        self.percent_var = tk.StringVar(value="0%")
        ttk.Label(frame, textvariable=self.percent_var).pack()

        # Warning label
        self.warning_var = tk.StringVar(value="⚠ This may slow down your computer while processing")
        ttk.Label(frame, textvariable=self.warning_var, foreground='orange').pack(pady=(10, 0))

        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(15, 0))

        self.start_btn = ttk.Button(btn_frame, text="Start Analysis", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._on_cancel)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_start(self):
        """Start the analysis process."""
        if self.total_pending == 0:
            messagebox.showinfo("No Screenshots", "No screenshots pending analysis.")
            self.window.destroy()
            return

        self.start_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Processing 0 of {self.total_pending}...")
        self.warning_var.set("Processing in progress...")

        # Start processing in background thread
        self._processing_thread = threading.Thread(
            target=self._run_analysis,
            daemon=True
        )
        self._processing_thread.start()

    def _run_analysis(self):
        """Run analysis in background thread."""
        try:
            self.night_processor.process_batch_with_progress(self.progress)
        except Exception as e:
            logging.error(f"Batch analysis error: {e}")
            self.progress.is_complete = True
        finally:
            self.window.after(0, self._on_complete)

    def _update_ui(self, progress: BatchAnalysisProgress):
        """Update UI from progress callback (called from background thread)."""
        def update():
            self.progress_bar['value'] = progress.percent_complete
            self.percent_var.set(f"{progress.percent_complete:.0f}%")
            self.status_var.set(
                f"Processing {progress.processed} of {progress.total}... "
                f"({progress.failed} failed)"
            )
        self.window.after(0, update)

    def _on_cancel(self):
        """Handle cancel button click."""
        self.progress.cancel()
        self.status_var.set("Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)

    def _on_complete(self):
        """Handle completion of analysis."""
        if self.progress.is_cancelled:
            msg = f"Cancelled after processing {self.progress.processed} screenshots."
        else:
            msg = f"Completed! Processed {self.progress.processed} screenshots ({self.progress.failed} failed)."

        self.status_var.set(msg)
        self.warning_var.set("")
        self.progress_bar['value'] = 100
        self.percent_var.set("Done")
        self.cancel_btn.config(text="Close", state=tk.NORMAL, command=self.window.destroy)
        self.start_btn.pack_forget()

    def _on_close(self):
        """Handle window close."""
        if self._processing_thread and self._processing_thread.is_alive():
            self.progress.cancel()
            # Wait briefly for thread to finish
            self._processing_thread.join(timeout=1.0)
        self.window.destroy()

    def show(self):
        """Show the dialog and wait for it to close."""
        self.window.grab_set()
        self.window.wait_window()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_batch_analysis_dialog.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/batch_analysis_dialog.py tests/test_batch_analysis_dialog.py && git commit -m "feat(8.6.3): add BatchAnalysisDialog with progress bar and cancel"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_night_processor.py tests/test_batch_analysis_dialog.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

This is sub-plan 2 of 3 for story 8.6.3. Next sub-plan:
- 035C: Tray menu integration
