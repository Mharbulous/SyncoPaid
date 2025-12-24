# Screenshot Retention & Cleanup - App Integration

> **TDD Required:** Each task: Write test → RED → Write code → GREEN → Commit

**Goal:** Integrate archiver with main app and add configuration options

**Approach:** Add archiver initialization to `__main__.py` startup and add archive-related config defaults.

**Tech Stack:** Existing syncopaid modules

---

**Story ID:** 2.6 | **Created:** 2025-12-22 | **Status:** `planned`

**Parent Plan:** 017_screenshot-retention-cleanup.md (Tasks 7-8 of 8)

**Depends On:** 017B_screenshot-retention-operations.md

---

## Prerequisites

- [x] venv activated: `venv\Scripts\activate`
- [x] Sub-plan A completed (core archive logic)
- [x] Sub-plan B completed (operations and scheduling)
- [x] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `tests/test_integration.py` | Create/Modify | Test app integration |
| `tests/test_config.py` | Modify | Test archive config |
| `src/syncopaid/__main__.py:147-160` | Modify | Initialize archiver on startup |
| `src/syncopaid/config.py:16-37` | Modify | Add archive config options |

## TDD Tasks

### Task 7: Integration with __main__.py

**Files:** Test: `tests/test_integration.py` | Impl: `src/syncopaid/__main__.py:147-160`

**RED:** Test app initializes archiver on startup.
```python
def test_app_initializes_archiver(mocker):
    mock_archiver = mocker.patch('syncopaid.archiver.ArchiveWorker')
    app = SyncoPaidApp()
    assert mock_archiver.called
    mock_archiver.return_value.run_once.assert_called_once()
```
Run: `pytest tests/test_integration.py::test_app_initializes_archiver -v` → Expect: FAILED

**GREEN:** Add archiver initialization to __main__.py.
```python
# In __main__.py after screenshot worker init
from syncopaid.archiver import ArchiveWorker

# Initialize archiver
screenshot_base_dir = get_screenshot_directory().parent
archive_dir = screenshot_base_dir / "archives"
self.archiver = ArchiveWorker(screenshot_base_dir, archive_dir)
self.archiver.run_once()  # Run on startup
self.archiver.start_background()  # Schedule monthly checks
```
Run: `pytest tests/test_integration.py::test_app_initializes_archiver -v` → Expect: PASSED

**COMMIT:** `git add tests/test_integration.py src/syncopaid/__main__.py && git commit -m "feat: integrate archiver into app startup"`

---

### Task 8: Add config options for archiving

**Files:** Test: `tests/test_config.py` | Impl: `src/syncopaid/config.py:16-37`

**RED:** Test config includes archive settings.
```python
def test_archive_config_defaults():
    config = Config()
    assert config.archive_enabled == True
    assert config.archive_check_interval_hours == 24
```
Run: `pytest tests/test_config.py::test_archive_config_defaults -v` → Expect: FAILED

**GREEN:** Add archive config to DEFAULT_CONFIG.
```python
# In config.py DEFAULT_CONFIG
"archive_enabled": True,
"archive_check_interval_hours": 24,
```
Run: `pytest tests/test_config.py::test_archive_config_defaults -v` → Expect: PASSED

**COMMIT:** `git add tests/test_config.py src/syncopaid/config.py && git commit -m "feat: add archive configuration options"`

---

## Verification

- [ ] All tests pass: `python -m pytest -v`
- [ ] Manual test: Create old folders, run app, verify archiving
- [ ] Manual test: Trigger archive error (disk full), verify dialog
- [ ] Check zip contents match original screenshots
- [ ] Verify monthly scheduling (mock system date)

## Notes

**Edge Cases:**
- Empty folders (skip archiving)
- Malformed folder names (ignore)
- Archives folder doesn't exist (create on init)
- Partial month at month boundary (excluded correctly)

**Follow-up Work:**
- Story 8.4.3 will use archives for screenshot retrieval in AI review UI
- Consider compression level tuning for disk space vs. CPU tradeoff
