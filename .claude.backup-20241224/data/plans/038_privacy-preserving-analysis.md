# Privacy-Preserving Analysis - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.6.4 | **Created:** 2025-12-23 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add privacy controls that confirm local-only AI processing, enable application exclusions from screenshot capture, and provide AI processing audit logs.

**Approach:** Extend Config dataclass with privacy-related fields, make SKIP_APPS configurable, add dedicated AI processing logger, and create a Settings dialog with Privacy tab displaying local processing guarantees.

**Tech Stack:** Python 3.11+, tkinter for UI, logging module, existing config.py/config_dataclass.py infrastructure

---

## Story Context

**Title:** Privacy-Preserving Analysis
**Description:** Confirm that screenshot analysis happens locally with attorney-client privilege compliance

**Acceptance Criteria:**
- [ ] Settings panel clearly states: "All AI processing happens locally on your device"
- [ ] No internet connection required for analysis
- [ ] No screenshots or extracted data leave the computer
- [ ] Option to view AI processing logs (for audit purposes)
- [ ] Option to exclude specific applications from screenshot capture

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Vision engine infrastructure exists (story 8.6.1)

## TDD Tasks

### Task 1: Add privacy config fields to Config dataclass (~3 min)

**Files:**
- Modify: `src/syncopaid/config_dataclass.py`
- Modify: `src/syncopaid/config_defaults.py`
- Test: `tests/test_config.py`

**Context:** The Config dataclass needs fields for screenshot exclusion apps and AI processing logging. These will be persisted to config.json and used by other components.

**Step 1 - RED:** Write failing test
```python
# tests/test_config.py - add to TestConfig class
def test_config_has_privacy_fields(self):
    """Test that Config has privacy-related fields."""
    from syncopaid.config_dataclass import Config

    config = Config()

    # Check field existence and defaults
    assert hasattr(config, 'screenshot_exclusion_apps')
    assert hasattr(config, 'ai_processing_logging_enabled')
    assert config.screenshot_exclusion_apps == []
    assert config.ai_processing_logging_enabled is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config.py::TestConfig::test_config_has_privacy_fields -v
```
Expected output: `FAILED` (AttributeError: 'Config' object has no attribute 'screenshot_exclusion_apps')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/config_dataclass.py - add fields after vision_engine fields (around line 165)
    # Privacy settings
    screenshot_exclusion_apps: List[str] = field(default_factory=list)
    ai_processing_logging_enabled: bool = True
```

Also update defaults:
```python
# src/syncopaid/config_defaults.py - add to DEFAULT_CONFIG dict
    "screenshot_exclusion_apps": [],
    "ai_processing_logging_enabled": True,
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py::TestConfig::test_config_has_privacy_fields -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/config_dataclass.py src/syncopaid/config_defaults.py tests/test_config.py && git commit -m "feat(8.6.4): add privacy config fields for exclusions and logging"
```

---

### Task 2: Make SKIP_APPS merge with config exclusions (~5 min)

**Files:**
- Modify: `src/syncopaid/screenshot_capture.py`
- Modify: `src/syncopaid/screenshot.py`
- Test: `tests/test_screenshot_capture.py`

**Context:** Currently SKIP_APPS is hardcoded. Screenshot capture should merge this with user-configured exclusions from config.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot_capture.py - add test
import pytest
from syncopaid.screenshot_capture import get_excluded_apps, SKIP_APPS


def test_get_excluded_apps_merges_config_with_skip_apps():
    """Test that get_excluded_apps combines SKIP_APPS with config exclusions."""
    config_exclusions = ["Notepad.exe", "Calculator.exe"]

    result = get_excluded_apps(config_exclusions)

    # Should include both hardcoded and config exclusions
    assert "LockApp.exe" in result  # From SKIP_APPS
    assert "Notepad.exe" in result  # From config
    assert "Calculator.exe" in result  # From config


def test_get_excluded_apps_handles_empty_config():
    """Test that empty config returns just SKIP_APPS."""
    result = get_excluded_apps([])

    assert result == SKIP_APPS
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot_capture.py::test_get_excluded_apps_merges_config_with_skip_apps -v
```
Expected output: `FAILED` (ImportError: cannot import name 'get_excluded_apps' from 'syncopaid.screenshot_capture')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/screenshot_capture.py - add function after SKIP_APPS definition (around line 46)
def get_excluded_apps(config_exclusions: list[str] | None = None) -> set[str]:
    """
    Get the combined set of apps to exclude from screenshot capture.

    Args:
        config_exclusions: Additional apps to exclude from user config

    Returns:
        Set of executable names to skip
    """
    if not config_exclusions:
        return SKIP_APPS
    return SKIP_APPS | set(config_exclusions)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot_capture.py::test_get_excluded_apps_merges_config_with_skip_apps -v
pytest tests/test_screenshot_capture.py::test_get_excluded_apps_handles_empty_config -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/screenshot_capture.py tests/test_screenshot_capture.py && git commit -m "feat(8.6.4): add get_excluded_apps function to merge config exclusions"
```

---

### Task 3: Update ScreenshotWorker to use config exclusions (~4 min)

**Files:**
- Modify: `src/syncopaid/screenshot.py`
- Test: `tests/test_screenshot.py`

**Context:** ScreenshotWorker currently checks only SKIP_APPS. It should use get_excluded_apps with config values.

**Step 1 - RED:** Write failing test
```python
# tests/test_screenshot.py - add test
from unittest.mock import Mock, patch


def test_screenshot_worker_respects_config_exclusions():
    """Test that ScreenshotWorker skips apps in config exclusions."""
    from syncopaid.screenshot import ScreenshotWorker
    from syncopaid.config_dataclass import Config

    # Config with custom exclusion
    config = Config(screenshot_exclusion_apps=["TestApp.exe"])

    worker = ScreenshotWorker(
        output_dir="test_output",
        config=config
    )

    # Check that config exclusions are loaded
    assert "TestApp.exe" in worker._excluded_apps
    assert "LockApp.exe" in worker._excluded_apps  # Still has hardcoded ones
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_screenshot.py::test_screenshot_worker_respects_config_exclusions -v
```
Expected output: `FAILED` (AttributeError: 'ScreenshotWorker' object has no attribute '_excluded_apps')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/screenshot.py - add import at top
from syncopaid.screenshot_capture import get_excluded_apps

# Modify ScreenshotWorker.__init__ to accept config and store excluded apps
# Add after self._config = config line (around line 70):
        self._excluded_apps = get_excluded_apps(
            config.screenshot_exclusion_apps if config else None
        )

# Modify the skip check in _capture_if_changed (around line 166):
# Replace: if window_app in SKIP_APPS:
# With:
        if window_app in self._excluded_apps:
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_screenshot.py::test_screenshot_worker_respects_config_exclusions -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/screenshot.py tests/test_screenshot.py && git commit -m "feat(8.6.4): integrate config exclusions into ScreenshotWorker"
```

---

### Task 4: Add AI processing logger infrastructure (~5 min)

**Files:**
- Create: `src/syncopaid/ai_processing_logger.py`
- Test: `tests/test_ai_processing_logger.py`

**Context:** A dedicated logger for AI processing audit trail. Logs to a file in the app data directory when enabled.

**Step 1 - RED:** Write failing test
```python
# tests/test_ai_processing_logger.py
import pytest
import tempfile
import os
from pathlib import Path


def test_ai_processing_logger_creates_log_file():
    """Test that AI processing logger creates log file when enabled."""
    from syncopaid.ai_processing_logger import setup_ai_processing_logger

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "ai_processing.log"

        logger = setup_ai_processing_logger(log_path, enabled=True)
        logger.info("Test log entry")

        assert log_path.exists()
        content = log_path.read_text()
        assert "Test log entry" in content


def test_ai_processing_logger_disabled_no_file():
    """Test that disabled logger does not create file."""
    from syncopaid.ai_processing_logger import setup_ai_processing_logger

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "ai_processing.log"

        logger = setup_ai_processing_logger(log_path, enabled=False)
        logger.info("This should not be logged to file")

        # File should not exist when disabled
        assert not log_path.exists()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_ai_processing_logger.py::test_ai_processing_logger_creates_log_file -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.ai_processing_logger')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/ai_processing_logger.py
"""AI processing audit logger for privacy compliance."""
import logging
from pathlib import Path
from typing import Optional


# Module-level logger name for AI processing audit
AI_PROCESSING_LOGGER_NAME = "syncopaid.ai_processing"


def setup_ai_processing_logger(
    log_path: Path,
    enabled: bool = True
) -> logging.Logger:
    """
    Configure the AI processing audit logger.

    Args:
        log_path: Path to the log file
        enabled: Whether to enable file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(AI_PROCESSING_LOGGER_NAME)
    logger.setLevel(logging.DEBUG if enabled else logging.CRITICAL)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    if enabled:
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Add file handler
        handler = logging.FileHandler(log_path, encoding='utf-8')
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Add null handler when disabled
        logger.addHandler(logging.NullHandler())

    return logger


def get_ai_processing_logger() -> logging.Logger:
    """Get the AI processing logger instance."""
    return logging.getLogger(AI_PROCESSING_LOGGER_NAME)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_ai_processing_logger.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/ai_processing_logger.py tests/test_ai_processing_logger.py && git commit -m "feat(8.6.4): add AI processing audit logger infrastructure"
```

---

### Task 5: Create privacy info panel data structure (~3 min)

**Files:**
- Create: `src/syncopaid/privacy_info.py`
- Test: `tests/test_privacy_info.py`

**Context:** A simple module providing the privacy information text to display in the settings panel. Centralizes the messaging for consistency.

**Step 1 - RED:** Write failing test
```python
# tests/test_privacy_info.py
import pytest


def test_privacy_info_provides_local_processing_statement():
    """Test that privacy info includes local processing statement."""
    from syncopaid.privacy_info import PRIVACY_STATEMENTS

    assert "local" in PRIVACY_STATEMENTS["processing_location"].lower()
    assert "device" in PRIVACY_STATEMENTS["processing_location"].lower()


def test_privacy_info_provides_no_network_statement():
    """Test that privacy info includes no network statement."""
    from syncopaid.privacy_info import PRIVACY_STATEMENTS

    assert "internet" in PRIVACY_STATEMENTS["network_requirement"].lower()
    assert "no" in PRIVACY_STATEMENTS["network_requirement"].lower() or \
           "not" in PRIVACY_STATEMENTS["network_requirement"].lower()


def test_privacy_info_provides_data_retention_statement():
    """Test that privacy info includes data retention statement."""
    from syncopaid.privacy_info import PRIVACY_STATEMENTS

    assert "leave" in PRIVACY_STATEMENTS["data_retention"].lower() or \
           "local" in PRIVACY_STATEMENTS["data_retention"].lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_privacy_info.py -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.privacy_info')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/privacy_info.py
"""Privacy information statements for UI display."""

# Privacy statements for settings panel display
PRIVACY_STATEMENTS = {
    "processing_location": (
        "All AI processing happens locally on your device. "
        "Screenshot analysis uses on-device models only."
    ),
    "network_requirement": (
        "No internet connection is required for analysis. "
        "The AI models run entirely offline."
    ),
    "data_retention": (
        "No screenshots or extracted data ever leave your computer. "
        "All data is stored locally in your user profile folder."
    ),
    "audit_logging": (
        "AI processing logs are available for audit purposes. "
        "View logs to verify what was analyzed and when."
    ),
    "app_exclusions": (
        "You can exclude specific applications from screenshot capture "
        "to protect sensitive content."
    ),
}

# Combined statement for compact display
PRIVACY_SUMMARY = """
🔒 Privacy-Preserving AI Analysis

• All AI processing happens locally on your device
• No internet connection required for analysis
• No screenshots or data leave your computer
• Optional audit logs for compliance verification
• Configurable application exclusions
"""
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_privacy_info.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/privacy_info.py tests/test_privacy_info.py && git commit -m "feat(8.6.4): add privacy info statements module"
```

---

### Task 6: Create Settings dialog with Privacy tab (~8 min)

**Files:**
- Create: `src/syncopaid/settings_dialog.py`
- Test: `tests/test_settings_dialog.py`

**Context:** A tkinter dialog with tabs for Privacy settings. Shows privacy statements, exclusion list management, and log viewer button.

**Step 1 - RED:** Write failing test
```python
# tests/test_settings_dialog.py
import pytest
from unittest.mock import MagicMock, patch


def test_settings_dialog_initializes():
    """Test SettingsDialog initializes without errors."""
    with patch('syncopaid.settings_dialog.tk.Toplevel'):
        from syncopaid.settings_dialog import SettingsDialog
        from syncopaid.config_dataclass import Config

        config = Config()
        mock_save = MagicMock()

        dialog = SettingsDialog(
            parent=None,
            config=config,
            on_save=mock_save
        )

        assert dialog.config == config


def test_settings_dialog_has_privacy_tab():
    """Test SettingsDialog has Privacy tab."""
    with patch('syncopaid.settings_dialog.tk.Toplevel'):
        with patch('syncopaid.settings_dialog.ttk.Notebook') as mock_notebook:
            from syncopaid.settings_dialog import SettingsDialog
            from syncopaid.config_dataclass import Config

            mock_nb_instance = MagicMock()
            mock_notebook.return_value = mock_nb_instance

            config = Config()
            dialog = SettingsDialog(parent=None, config=config, on_save=MagicMock())

            # Verify add was called with "Privacy" tab
            add_calls = [str(call) for call in mock_nb_instance.add.call_args_list]
            assert any("Privacy" in str(call) for call in add_calls)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_settings_dialog.py::test_settings_dialog_initializes -v
```
Expected output: `FAILED` (ModuleNotFoundError: No module named 'syncopaid.settings_dialog')

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/settings_dialog.py
"""Settings dialog with privacy controls."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from syncopaid.config_dataclass import Config
from syncopaid.privacy_info import PRIVACY_STATEMENTS, PRIVACY_SUMMARY
from syncopaid.config_paths import get_user_data_path


class SettingsDialog:
    """
    Settings dialog with Privacy tab for configuring:
    - View privacy statements
    - Manage application exclusions
    - Access AI processing logs
    """

    def __init__(
        self,
        parent: Optional[tk.Tk],
        config: Config,
        on_save: Callable[[Config], None]
    ):
        """
        Initialize settings dialog.

        Args:
            parent: Parent tkinter window (or None for standalone)
            config: Current configuration
            on_save: Callback when settings are saved
        """
        self.config = config
        self.on_save = on_save
        self._exclusion_list: list[str] = list(config.screenshot_exclusion_apps)

        self._create_window(parent)

    def _create_window(self, parent: Optional[tk.Tk]):
        """Create the dialog window."""
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("SyncoPaid Settings")
        self.window.geometry("500x450")
        self.window.resizable(False, False)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add Privacy tab
        self._create_privacy_tab()

        # Button frame at bottom
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Save", command=self._on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)

    def _create_privacy_tab(self):
        """Create the Privacy settings tab."""
        privacy_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(privacy_frame, text="Privacy")

        # Privacy summary section
        summary_label = ttk.Label(
            privacy_frame,
            text=PRIVACY_SUMMARY.strip(),
            justify=tk.LEFT,
            wraplength=450
        )
        summary_label.pack(fill=tk.X, pady=(0, 15))

        # Separator
        ttk.Separator(privacy_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # AI Processing Logging section
        log_frame = ttk.LabelFrame(privacy_frame, text="AI Processing Logs", padding=10)
        log_frame.pack(fill=tk.X, pady=10)

        self.logging_var = tk.BooleanVar(value=self.config.ai_processing_logging_enabled)
        ttk.Checkbutton(
            log_frame,
            text="Enable AI processing audit logs",
            variable=self.logging_var
        ).pack(anchor=tk.W)

        ttk.Button(
            log_frame,
            text="View Processing Logs",
            command=self._view_logs
        ).pack(anchor=tk.W, pady=(10, 0))

        # Application Exclusions section
        exclusion_frame = ttk.LabelFrame(privacy_frame, text="Application Exclusions", padding=10)
        exclusion_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(
            exclusion_frame,
            text="These applications will not be captured in screenshots:"
        ).pack(anchor=tk.W)

        # Listbox with scrollbar
        list_frame = ttk.Frame(exclusion_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.exclusion_listbox = tk.Listbox(
            list_frame,
            height=5,
            yscrollcommand=scrollbar.set
        )
        self.exclusion_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.exclusion_listbox.yview)

        # Populate listbox
        for app in self._exclusion_list:
            self.exclusion_listbox.insert(tk.END, app)

        # Add/Remove buttons
        btn_row = ttk.Frame(exclusion_frame)
        btn_row.pack(fill=tk.X)

        ttk.Button(btn_row, text="Add...", command=self._add_exclusion).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="Remove", command=self._remove_exclusion).pack(side=tk.LEFT, padx=2)

    def _view_logs(self):
        """Open the AI processing log file."""
        log_path = get_user_data_path() / "ai_processing.log"

        if not log_path.exists():
            messagebox.showinfo(
                "No Logs",
                "No AI processing logs exist yet.\n\n"
                "Logs will be created when screenshot analysis runs."
            )
            return

        # Open with default text editor
        if sys.platform == "win32":
            os.startfile(log_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(log_path)])
        else:
            subprocess.run(["xdg-open", str(log_path)])

    def _add_exclusion(self):
        """Add an application to the exclusion list."""
        app_name = tk.simpledialog.askstring(
            "Add Application",
            "Enter the executable name (e.g., notepad.exe):",
            parent=self.window
        )

        if app_name and app_name.strip():
            app_name = app_name.strip()
            if app_name not in self._exclusion_list:
                self._exclusion_list.append(app_name)
                self.exclusion_listbox.insert(tk.END, app_name)

    def _remove_exclusion(self):
        """Remove selected application from exclusion list."""
        selection = self.exclusion_listbox.curselection()
        if selection:
            index = selection[0]
            self.exclusion_listbox.delete(index)
            del self._exclusion_list[index]

    def _on_save(self):
        """Save settings and close dialog."""
        # Update config with new values
        self.config.ai_processing_logging_enabled = self.logging_var.get()
        self.config.screenshot_exclusion_apps = self._exclusion_list.copy()

        # Call save callback
        self.on_save(self.config)

        messagebox.showinfo("Settings Saved", "Your settings have been saved.")
        self.window.destroy()

    def show(self):
        """Show the dialog and wait for it to close."""
        self.window.grab_set()
        self.window.wait_window()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_settings_dialog.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/settings_dialog.py tests/test_settings_dialog.py && git commit -m "feat(8.6.4): add SettingsDialog with Privacy tab and exclusion management"
```

---

### Task 7: Wire up Settings menu item (~4 min)

**Files:**
- Modify: `src/syncopaid/tray.py`
- Modify: `src/syncopaid/main_app_class.py`
- Test: Manual verification

**Context:** Add "Settings" to the tray menu and wire it to show the SettingsDialog.

**Step 1 - Implementation:**

First, add callback to TrayIcon:
```python
# src/syncopaid/tray.py - modify __init__ parameter list (around line 40)
# Add parameter:
    on_settings: Optional[Callable] = None,

# Add to instance variables (around line 55):
    self.on_settings = on_settings or (lambda: None)
```

Then add menu item in `_create_menu`:
```python
# src/syncopaid/tray.py - in _create_menu method, add after "Open SyncoPaid" item:
        pystray.MenuItem("⚙ Settings", self._handle_settings),
```

Add handler method:
```python
# src/syncopaid/tray.py - add handler method (in TrayMenuHandlers mixin or TrayIcon)
def _handle_settings(self, icon=None, item=None):
    """Handle 'Settings' menu item click."""
    if hasattr(self, 'on_settings'):
        self.on_settings()
```

Then wire up in SyncoPaidApp:
```python
# src/syncopaid/main_app_class.py - add import at top
from syncopaid.settings_dialog import SettingsDialog

# Modify TrayIcon instantiation to pass callback (around line 80):
self.tray = TrayIcon(
    # ... existing callbacks ...
    on_settings=self.show_settings_dialog,
)

# Add method to SyncoPaidApp class:
def show_settings_dialog(self):
    """Show the settings dialog."""
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()

    def save_config(config):
        self.config_manager.save(config)
        # Reload config in components that need it
        if self.screenshot_worker:
            self.screenshot_worker._excluded_apps = get_excluded_apps(
                config.screenshot_exclusion_apps
            )

    dialog = SettingsDialog(
        parent=root,
        config=self.config,
        on_save=save_config
    )
    dialog.show()

    root.destroy()
```

**Step 2 - Verify:** Manual test
```bash
python -m syncopaid
# Right-click tray icon, verify "Settings" menu item appears
# Click Settings, verify Privacy tab shows
```

**Step 3 - COMMIT:**
```bash
git add src/syncopaid/tray.py src/syncopaid/main_app_class.py && git commit -m "feat(8.6.4): add Settings menu item and wire to SettingsDialog"
```

---

### Task 8: Initialize AI processing logger on app startup (~3 min)

**Files:**
- Modify: `src/syncopaid/main_app_class.py`
- Test: `tests/test_main_app.py`

**Context:** Set up the AI processing logger when the application starts, respecting the config setting.

**Step 1 - RED:** Write failing test
```python
# tests/test_main_app.py - add test
import pytest
from unittest.mock import patch, MagicMock


def test_app_initializes_ai_processing_logger():
    """Test that app sets up AI processing logger on init."""
    with patch('syncopaid.main_app_class.setup_ai_processing_logger') as mock_setup:
        with patch('syncopaid.main_app_class.TrayIcon'):
            with patch('syncopaid.main_app_class.Database'):
                from syncopaid.main_app_class import SyncoPaidApp
                from syncopaid.config_dataclass import Config

                config = Config(ai_processing_logging_enabled=True)

                # Create app with mock config manager
                mock_config_manager = MagicMock()
                mock_config_manager.load.return_value = config

                app = SyncoPaidApp(config_manager=mock_config_manager)

                # Verify logger was set up
                mock_setup.assert_called_once()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_main_app.py::test_app_initializes_ai_processing_logger -v
```
Expected output: `FAILED` (setup_ai_processing_logger not imported or called)

**Step 3 - GREEN:** Write minimal implementation
```python
# src/syncopaid/main_app_class.py - add import at top
from syncopaid.ai_processing_logger import setup_ai_processing_logger
from syncopaid.config_paths import get_user_data_path

# In SyncoPaidApp.__init__, add after config loading:
        # Set up AI processing logger
        log_path = get_user_data_path() / "ai_processing.log"
        setup_ai_processing_logger(
            log_path=log_path,
            enabled=self.config.ai_processing_logging_enabled
        )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_main_app.py::test_app_initializes_ai_processing_logger -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/main_app_class.py tests/test_main_app.py && git commit -m "feat(8.6.4): initialize AI processing logger on app startup"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid                    # Application runs
# Right-click tray icon
# Click "Settings"
# Verify Privacy tab shows privacy statements
# Add an app to exclusions, save, verify it persists
# Check that ai_processing.log exists in app data folder
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

**Dependencies:**
- Story 8.6.1 must complete for actual AI processing logs to have content
- Until then, the log file will exist but be empty or minimal

**Edge Cases:**
- Missing config.json: Defaults ensure privacy fields exist
- Large exclusion list: Listbox handles scrolling
- Log file very large: Opens in default editor, user can manage

**Future Work:**
- Story 8.6.5: Integrate failed analysis tracking with AI processing logs
- Consider log rotation for very long-running installations
