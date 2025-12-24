# Batch Processing On-Demand - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.3 | **Created:** 2025-12-23 | **Stage:** `decomposed`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add "Analyze Now" menu option that triggers screenshot analysis on-demand with progress tracking and cancellation support.

**Approach:** Extend the existing NightProcessor with progress callbacks and cancellation tokens, add a progress dialog UI, and integrate with the system tray menu.

**Tech Stack:** Python 3.11+, tkinter for UI, pystray for tray menu, threading for background processing

---

## DECOMPOSED

This plan has been decomposed into sub-plans:
- 035A_batch-analysis-foundation.md - Tasks 1-2: Database method + BatchAnalysisProgress dataclass
- 035B_batch-analysis-processor-ui.md - Tasks 3-4: NightProcessor progress method + BatchAnalysisDialog
- 035C_batch-analysis-tray-integration.md - Tasks 5-6: Tray menu integration

---

## Story Context

**Title:** Batch Processing On-Demand
**Description:** Manual trigger for screenshot analysis

**Acceptance Criteria:**
- [ ] Button/menu option: "Analyze Now"
- [ ] Shows progress indicator (X of Y screenshots processed)
- [ ] Can cancel mid-processing
- [ ] System remains responsive during processing (background thread)
- [ ] Warns if this will slow down computer performance

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Story 8.6.1 (Automatic Screenshot Analysis) infrastructure exists

**Note:** This story depends on database methods `get_pending_screenshot_count()` and screenshot analyzer infrastructure. If these are missing, the implementation will add stub/placeholder methods that can be completed when 8.6.1 is fully verified.

## TDD Tasks

### Task 1: Add get_pending_screenshot_count to Database (~5 min)

**Files:**
- Modify: `src/syncopaid/database_screenshots.py`
- Test: `tests/test_database_screenshots.py`

**Context:** The NightProcessor needs to know how many screenshots are pending analysis. This method queries the database for screenshots with `analysis_status = 'pending'` or NULL.

**Step 1 - RED:** Write failing test
```python
# tests/test_database_screenshots.py - add to existing test class
def test_get_pending_screenshot_count_returns_count(self, db_with_screenshots):
    """Test that get_pending_screenshot_count returns correct count."""
    # Arrange: db_with_screenshots fixture creates 3 screenshots with NULL analysis_status

    # Act
    count = db_with_screenshots.get_pending_screenshot_count()

    # Assert
    assert count == 3


def test_get_pending_screenshot_count_excludes_completed(self, db_with_screenshots):
    """Test that completed screenshots are not counted."""
    # Arrange: Update one screenshot to 'completed'
    db_with_screenshots.conn.execute(
        "UPDATE screenshots SET analysis_status = 'completed' WHERE id = 1"
    )
    db_with_screenshots.conn.commit()

    # Act
    count = db_with_screenshots.get_pending_screenshot_count()

    # Assert
    assert count == 2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_database_screenshots.py::test_get_pending_screenshot_count_returns_count -v
```
Expected output: `FAILED` (AttributeError: 'Database' object has no attribute 'get_pending_screenshot_count')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/database_screenshots.py - add method to DatabaseScreenshotsMixin
def get_pending_screenshot_count(self) -> int:
    """
    Get count of screenshots pending analysis.

    Returns:
        Number of screenshots with analysis_status NULL or 'pending'
    """
    cursor = self.conn.execute("""
        SELECT COUNT(*) FROM screenshots
        WHERE analysis_status IS NULL OR analysis_status = 'pending'
    """)
    return cursor.fetchone()[0]
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_database_screenshots.py::test_get_pending_screenshot_count_returns_count -v
pytest tests/test_database_screenshots.py::test_get_pending_screenshot_count_excludes_completed -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_database_screenshots.py src/syncopaid/database_screenshots.py && git commit -m "feat(8.6.3): add get_pending_screenshot_count database method"
```

---

### Task 2: Create BatchAnalysisProgress dataclass (~3 min)

**Files:**
- Create: `src/syncopaid/batch_analysis_progress.py`
- Test: `tests/test_batch_analysis_progress.py`

**Context:** A dataclass to track batch analysis progress, supporting callbacks and cancellation. This decouples progress tracking from the NightProcessor.

**Step 1 - RED:** Write failing test
```python
# tests/test_batch_analysis_progress.py
import pytest
from syncopaid.batch_analysis_progress import BatchAnalysisProgress


def test_progress_initialization():
    """Test BatchAnalysisProgress initializes with correct values."""
    progress = BatchAnalysisProgress(total=100)

    assert progress.total == 100
    assert progress.processed == 0
    assert progress.failed == 0
    assert progress.is_cancelled is False
    assert progress.is_complete is False


def test_progress_update():
    """Test progress can be updated."""
    progress = BatchAnalysisProgress(total=10)

    progress.processed = 5
    progress.failed = 1

    assert progress.processed == 5
    assert progress.failed == 1
    assert progress.percent_complete == 50.0


def test_progress_cancel():
    """Test cancellation flag."""
    progress = BatchAnalysisProgress(total=10)

    progress.cancel()

    assert progress.is_cancelled is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_batch_analysis_progress.py -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.batch_analysis_progress')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/batch_analysis_progress.py
"""Batch analysis progress tracking."""
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class BatchAnalysisProgress:
    """
    Tracks progress of batch screenshot analysis.

    Attributes:
        total: Total screenshots to process
        processed: Number successfully processed
        failed: Number that failed
        is_cancelled: True if user cancelled
        is_complete: True when processing finished
        on_progress: Optional callback for progress updates
    """
    total: int
    processed: int = 0
    failed: int = 0
    is_cancelled: bool = False
    is_complete: bool = False
    on_progress: Optional[Callable[['BatchAnalysisProgress'], None]] = field(default=None, repr=False)

    @property
    def percent_complete(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.processed / self.total) * 100.0

    def cancel(self):
        """Request cancellation of processing."""
        self.is_cancelled = True

    def update(self, processed: int = None, failed: int = None):
        """Update progress and trigger callback."""
        if processed is not None:
            self.processed = processed
        if failed is not None:
            self.failed = failed
        if self.on_progress:
            self.on_progress(self)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_batch_analysis_progress.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/batch_analysis_progress.py tests/test_batch_analysis_progress.py && git commit -m "feat(8.6.3): add BatchAnalysisProgress dataclass for progress tracking"
```

---

### Task 3: Add process_batch_with_progress to NightProcessor (~5 min)

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

### Task 4: Create BatchAnalysisDialog UI (~8 min)

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

### Task 5: Add "Analyze Now" to tray menu (~5 min)

**Files:**
- Modify: `src/syncopaid/tray.py`
- Modify: `src/syncopaid/main_app_class.py`
- Test: Manual verification (tray menu is interactive)

**Context:** Add menu item to system tray that opens the BatchAnalysisDialog. This connects the UI to the NightProcessor infrastructure.

**Step 1 - RED:** Manual verification - menu item does not exist

**Step 2 - Implementation:**

First, add callback to TrayIcon:
```python
# src/syncopaid/tray.py - modify __init__ to add callback parameter
def __init__(
    self,
    on_start: Optional[Callable] = None,
    on_pause: Optional[Callable] = None,
    on_open: Optional[Callable] = None,
    on_quit: Optional[Callable] = None,
    on_analyze: Optional[Callable] = None,  # NEW
    config_manager=None
):
    # ... existing code ...
    self.on_analyze = on_analyze or (lambda: None)  # NEW
```

Then, add menu item in `_create_menu`:
```python
# src/syncopaid/tray.py - modify _create_menu method
def _create_menu(self):
    """Create the right-click menu."""
    if not TRAY_AVAILABLE:
        return None

    return pystray.Menu(
        pystray.MenuItem(
            lambda text: "⏸ Pause Tracking" if self.is_tracking else "▶ Start Tracking",
            self._toggle_tracking,
            default=True
        ),
        pystray.MenuItem("📊 Open SyncoPaid", self._handle_open),
        pystray.MenuItem("🔍 Analyze Now", self._handle_analyze),  # NEW
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "🚀 Start with Windows",
            self._toggle_startup,
            checked=lambda item: is_startup_enabled()
        ),
        pystray.MenuItem("ℹ About", self._handle_about)
    )

# Add handler method (in TrayMenuHandlers mixin or TrayIcon class)
def _handle_analyze(self, icon=None, item=None):
    """Handle 'Analyze Now' menu click."""
    self.on_analyze()
```

Then, add method to SyncoPaidApp:
```python
# src/syncopaid/main_app_class.py - add import at top
from syncopaid.batch_analysis_dialog import BatchAnalysisDialog

# Modify __init__ to pass callback to TrayIcon
self.tray = TrayIcon(
    on_start=self.start_tracking,
    on_pause=self.pause_tracking,
    on_open=self.show_main_window,
    on_quit=self.quit_app,
    on_analyze=self.show_analyze_dialog,  # NEW
    config_manager=self.config_manager
)

# Add method to SyncoPaidApp class
def show_analyze_dialog(self):
    """Show the batch analysis dialog."""
    if not self.night_processor:
        logging.warning("Night processor not enabled - cannot analyze")
        return

    # Create root window if needed (for standalone dialog)
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide root window

    dialog = BatchAnalysisDialog(
        parent=root,
        night_processor=self.night_processor,
        get_pending_count=self.database.get_pending_screenshot_count
    )
    dialog.show()

    root.destroy()
```

**Step 3 - Verify GREEN:** Manual test
```bash
python -m syncopaid
# Right-click tray icon, verify "Analyze Now" menu item appears
```

**Step 4 - COMMIT:**
```bash
git add src/syncopaid/tray.py src/syncopaid/main_app_class.py && git commit -m "feat(8.6.3): add Analyze Now menu item to system tray"
```

---

### Task 6: Add analyze callback to tray_menu_handlers (~3 min)

**Files:**
- Modify: `src/syncopaid/tray_menu_handlers.py`

**Context:** The TrayMenuHandlers mixin needs the `_handle_analyze` method to complete the integration.

**Step 1 - Implementation:**
```python
# src/syncopaid/tray_menu_handlers.py - add method
def _handle_analyze(self, icon=None, item=None):
    """Handle 'Analyze Now' menu item click."""
    if hasattr(self, 'on_analyze'):
        self.on_analyze()
```

**Step 2 - Verify:** Run application and click menu item

**Step 3 - COMMIT:**
```bash
git add src/syncopaid/tray_menu_handlers.py && git commit -m "feat(8.6.3): add _handle_analyze to tray menu handlers"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid                    # Application runs
# Right-click tray icon
# Click "Analyze Now"
# Verify dialog shows with progress bar
# Verify cancel button works
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

**Dependencies:**
- Story 8.6.1 must complete for actual screenshot analysis to work
- Until then, `process_batch` may return 0 (no-op)
- The UI and progress tracking infrastructure will be ready

**Edge Cases:**
- Zero pending screenshots: Show info dialog and close
- Analysis already running: Prevent starting another
- Window closed during processing: Cancel gracefully

**Future Work:**
- Story 8.6.4: Privacy settings integration
- Story 8.6.5: Failed analysis handling in dialog
