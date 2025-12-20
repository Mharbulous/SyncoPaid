# 040: Command Line Tracking - get_active_window Update

## Task
Update `get_active_window()` to capture and return redacted command line arguments.

## Context
The get_active_window() function is called every poll interval. It needs to extract command line and apply redaction before returning.

## Scope
- Add 'cmdline' key to return dictionary
- Call get_process_cmdline() to get raw cmdline
- Apply redact_sensitive_paths() before returning

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/tracker.py` | Modify get_active_window() |
| `tests/test_cmdline_tracking.py` | Add tests |

## Implementation

```python
# src/syncopaid/tracker.py - modify get_active_window()
def get_active_window() -> Dict[str, Optional[str]]:
    """
    Get information about the currently active foreground window.
    Now includes redacted cmdline for instance differentiation.
    """
    if not WINDOWS_APIS_AVAILABLE:
        # Mock data for testing
        import random
        mock_apps = [
            ("WINWORD.EXE", "Document.docx - Word", ["WINWORD.EXE", "[PATH]\\Document.docx"]),
            ("chrome.exe", "Google Chrome", ["chrome.exe", "--profile-directory=Default"]),
        ]
        app, title, cmdline = random.choice(mock_apps)
        return {"app": app, "title": title, "pid": 0, "cmdline": cmdline}

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        if pid < 0:
            pid = pid & 0xFFFFFFFF

        process_name = None
        cmdline = None

        try:
            process = psutil.Process(pid)
            process_name = process.name()
            raw_cmdline = process.cmdline()
            if raw_cmdline:
                cmdline = redact_sensitive_paths(raw_cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            pass

        return {"app": process_name, "title": title, "pid": pid, "cmdline": cmdline}

    except Exception as e:
        logging.error(f"Error getting active window: {e}")
        return {"app": None, "title": None, "pid": None, "cmdline": None}
```

### Tests

```python
# tests/test_cmdline_tracking.py (add)
def test_get_active_window_includes_cmdline():
    from syncopaid.tracker import get_active_window

    with patch('syncopaid.tracker.WINDOWS_APIS_AVAILABLE', False):
        result = get_active_window()

    assert 'cmdline' in result
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_cmdline_tracking.py::test_get_active_window_includes_cmdline -v
python -m syncopaid.tracker  # 30s manual test
```

## Dependencies
- Task 039 (helper functions)

## Next Task
After this: `041_cmdline-tracker-loop.md`
