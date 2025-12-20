# 012B: Command Line Tracking - Helper Functions

## Task
Implement `get_process_cmdline()` and `redact_sensitive_paths()` functions.

## Context
These helper functions extract command line from a process and redact sensitive file paths before storage. Handles errors gracefully and protects attorney-client privilege.

## Scope
- get_process_cmdline(pid) - safely get cmdline from psutil
- redact_sensitive_paths(cmdline) - redact paths but preserve useful flags

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/tracker.py` | Add helper functions |
| `tests/test_cmdline_tracking.py` | Add tests |

## Implementation

### get_process_cmdline

```python
# src/syncopaid/tracker.py (add after get_idle_seconds)
def get_process_cmdline(pid: int) -> Optional[List[str]]:
    """
    Get command line arguments for a process by PID.
    Returns None if unavailable (AccessDenied, NoSuchProcess, etc.)
    """
    if not WINDOWS_APIS_AVAILABLE:
        return None

    try:
        process = psutil.Process(pid)
        cmdline = process.cmdline()
        return cmdline if cmdline else None
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError):
        return None
    except Exception as e:
        logging.debug(f"Error getting cmdline for PID {pid}: {e}")
        return None
```

### redact_sensitive_paths

```python
# src/syncopaid/tracker.py (add after get_process_cmdline)
def redact_sensitive_paths(cmdline: List[str]) -> List[str]:
    """
    Redact sensitive file paths from command line arguments.
    Preserves profile flags, redacts user paths.
    """
    if not cmdline:
        return []

    import re
    import os

    result = []
    path_pattern = re.compile(r'^[A-Za-z]:\\')
    user_pattern = re.compile(r'\\Users\\[^\\]+\\', re.IGNORECASE)

    for arg in cmdline:
        if not arg:
            continue

        # Preserve profile directory flags
        if arg.startswith('--profile-directory=') or arg.startswith('--profile='):
            result.append(arg)
            continue

        # Redact file paths
        if path_pattern.match(arg):
            filename = os.path.basename(arg)
            if user_pattern.search(arg):
                result.append(f"[REDACTED_PATH]\\{filename}")
            else:
                result.append(f"[PATH]\\{filename}")
            continue

        result.append(arg)

    return result
```

### Tests

```python
# tests/test_cmdline_tracking.py (add)
from unittest.mock import patch, MagicMock


def test_get_process_cmdline_returns_list():
    from syncopaid.tracker import get_process_cmdline
    mock_process = MagicMock()
    mock_process.cmdline.return_value = ["chrome.exe", "--profile-directory=Default"]

    with patch('syncopaid.tracker.psutil.Process', return_value=mock_process):
        result = get_process_cmdline(1234)

    assert result == ["chrome.exe", "--profile-directory=Default"]


def test_get_process_cmdline_handles_access_denied():
    from syncopaid.tracker import get_process_cmdline
    import psutil

    with patch('syncopaid.tracker.psutil.Process', side_effect=psutil.AccessDenied()):
        result = get_process_cmdline(1234)

    assert result is None


def test_redact_sensitive_paths_preserves_profile():
    from syncopaid.tracker import redact_sensitive_paths
    cmdline = ["chrome.exe", "--profile-directory=Work", "--flag"]
    result = redact_sensitive_paths(cmdline)
    assert "--profile-directory=Work" in result


def test_redact_sensitive_paths_redacts_file_paths():
    from syncopaid.tracker import redact_sensitive_paths
    cmdline = ["WINWORD.EXE", "C:\\Users\\Brahm\\Documents\\secret.docx"]
    result = redact_sensitive_paths(cmdline)
    assert "Brahm" not in str(result)
    assert "secret.docx" in str(result)
```

## Verification

```bash
venv\Scripts\activate
pytest tests/test_cmdline_tracking.py -v
```

## Dependencies
- Task 012A (ActivityEvent field)

## Next Task
After this: `012C_cmdline-active-window.md`
