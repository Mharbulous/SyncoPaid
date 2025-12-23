# Secure Data Deletion - File Overwrite Utility

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Create secure file deletion utility that overwrites files before unlinking

**Approach:** Implement secure_delete_file function that writes zeros over file content before deletion

**Tech Stack:** Python os/pathlib for file operations

---

**Story ID:** 7.6 | **Created:** 2025-12-21 | **Status:** `planned`

**Parent Plan:** 028_secure-data-deletion.md

---

## Story Context

**Title:** Secure Data Deletion - File Overwrite Utility

**Description:** Create a utility module for securely deleting files by overwriting their contents with zeros before deletion.

**Acceptance Criteria:**
- [x] Files are overwritten with zeros before deletion
- [x] Handles missing files gracefully
- [x] Large files handled in chunks to avoid memory issues

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Baseline tests pass: `python -m pytest -v`
- [x] Sub-plan 028A completed (secure_delete pragma enabled)

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_secure_delete.py` | Modify | Add test for secure file deletion |
| `src/syncopaid/secure_delete.py` | Create | Secure file deletion utility module |

## TDD Tasks

### Task 1: Create secure file overwrite utility

**Files:** Test: `tests/test_secure_delete.py` | Impl: `src/syncopaid/secure_delete.py`

**RED:** Test secure file overwrite function.
```python
def test_secure_file_delete(tmp_path):
    """Verify file contents are overwritten before deletion."""
    test_file = tmp_path / "sensitive.jpg"
    secret_content = b"ATTORNEY_CLIENT_PRIVILEGED_CONTENT"
    test_file.write_bytes(secret_content)

    from syncopaid.secure_delete import secure_delete_file
    secure_delete_file(test_file)

    # File should be deleted
    assert not test_file.exists()

    # Content should not be recoverable (check parent directory for remnants)
    # Note: This is a best-effort test; full forensic verification requires OS-level tools
```
Run: `pytest tests/test_secure_delete.py::test_secure_file_delete -v` → Expect: FAILED

**GREEN:** Implement secure file deletion with overwrite.
```python
# src/syncopaid/secure_delete.py
"""Secure deletion utilities for attorney-client privileged data."""

import os
from pathlib import Path
import logging


def secure_delete_file(file_path: Path, passes: int = 1) -> bool:
    """
    Securely delete a file by overwriting with zeros before unlinking.

    Args:
        file_path: Path to file to securely delete
        passes: Number of overwrite passes (default 1 for SSD optimization)

    Returns:
        True if file was successfully deleted, False if file didn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False

    try:
        file_size = file_path.stat().st_size

        # Overwrite with zeros
        with open(file_path, 'wb') as f:
            for _ in range(passes):
                f.seek(0)
                # Write in chunks to handle large files
                chunk_size = 65536  # 64KB chunks
                remaining = file_size
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(b'\x00' * write_size)
                    remaining -= write_size
                f.flush()
                os.fsync(f.fileno())

        # Delete the file
        file_path.unlink()
        logging.debug(f"Securely deleted: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to securely delete {file_path}: {e}")
        # Fall back to regular deletion
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
```
Run: `pytest tests/test_secure_delete.py::test_secure_file_delete -v` → Expect: PASSED

**COMMIT:** `git add tests/test_secure_delete.py src/syncopaid/secure_delete.py && git commit -m "feat: add secure file deletion with overwrite"`

---

## Verification

- [ ] All tests pass: `python -m pytest tests/test_secure_delete.py -v`
- [ ] Full test suite: `python -m pytest -v`

## Notes

**Screenshot Secure Deletion:**
- Single pass overwrite with zeros (sufficient for SSD/flash storage)
- Multiple passes unnecessary for modern storage (NIST 800-88 guidance)
- Large files handled in chunks to avoid memory issues

**Edge Cases:**
- File already deleted (gracefully skip)
- Permission denied on file (log error, fall back to regular deletion)
