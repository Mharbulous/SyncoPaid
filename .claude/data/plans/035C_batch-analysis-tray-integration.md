# Batch Analysis Tray Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.3 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 035_batch-processing-on-demand.md

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add "Analyze Now" menu option to system tray that opens the BatchAnalysisDialog.

**Approach:** Extend TrayIcon with new callback, add menu item, connect to SyncoPaidApp.

**Tech Stack:** Python 3.11+, pystray for tray menu, tkinter for dialog

---

## Story Context

**Title:** Batch Processing On-Demand (Part 3 of 3)
**Description:** Integration layer - tray menu and app wiring

**Acceptance Criteria:**
- [ ] "Analyze Now" menu item in system tray
- [ ] Menu item opens BatchAnalysisDialog
- [ ] Dialog receives NightProcessor and database references

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Sub-plan 035A completed (BatchAnalysisProgress dataclass exists)
- [ ] Sub-plan 035B completed (BatchAnalysisDialog and NightProcessor.process_batch_with_progress exist)

## TDD Tasks

### Task 1: Add "Analyze Now" to tray menu (~5 min)

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

### Task 2: Add analyze callback to tray_menu_handlers (~3 min)

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
