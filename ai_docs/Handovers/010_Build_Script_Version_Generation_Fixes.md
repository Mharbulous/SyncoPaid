# Handover: Build Script Version Generation Fixes

**From**: Opus 4.5
**To**: Sonnet 4.5
**Date**: 2025-12-10
**Branch**: `claude/review-build-script-01MxSJ1qnfa5J47eFUnL6fMn`

## Task Summary

Fix flaws in the automatic version generation system for PyInstaller builds. The current implementation (commits `ab5856b` and `c28e804`) has design issues causing dirty working trees and commit hash mismatches.

---

## Issues Identified (Priority Order)

### 1. Generated files tracked by git

**Files affected:**
- `version_info.txt` - Listed in `.gitignore:37` but was committed BEFORE the ignore rule, so still tracked
- `lawtime/__init__.py` - Modified at build time with commit hash, causing uncommitted changes after every build

**Fix:**
- Run `git rm --cached version_info.txt`
- Refactor to NOT modify `__init__.py` at build time

### 2. Chicken-and-egg commit hash problem

Build embeds current commit hash → then user commits → executable has OLD hash. The binary never reflects its own commit.

**Fix options:**
- Use git tags for releases (detect with `git describe --tags`)
- Accept this as expected dev behavior, clearly document it
- Create separate `lawtime/_version.py` (gitignored), import with fallback in `__init__.py`

### 3. Windows path separator in spec file

`TimeLogger.spec:5` uses `lawtime\\__main__.py` - breaks on Linux/macOS builds.

**Fix:** Change to forward slash `lawtime/__main__.py`

---

## Key Files

| File | Purpose | Notes |
|------|---------|-------|
| `generate_version.py` | Main script - reads VERSION, gets git hash, generates version_info.txt, modifies __init__.py | Lines 159-200 are the problem area |
| `VERSION` | Contains `1.0.0` | Single source of truth - this is correct |
| `TimeLogger.spec` | PyInstaller config | Line 43 references version_info.txt |
| `build.sh` / `build.bat` | Build scripts | Call generate_version.py before pyinstaller |
| `lawtime/__init__.py` | Package init | Currently has hardcoded hash `1.0.0.ab5856b` |
| `.gitignore:37` | Has `version_info.txt` | Ineffective because file already tracked |

---

## Recommended Implementation

### Approach: Gitignored `_version.py` with fallback

1. **Create `lawtime/_version.py`** (gitignored) at build time:
```python
# Auto-generated - DO NOT COMMIT
__version__ = "1.0.0.c28e804"
__product_version__ = "1.0.0"
```

2. **Modify `lawtime/__init__.py`** to import with fallback:
```python
try:
    from lawtime._version import __version__, __product_version__
except ImportError:
    __version__ = "0.0.0.dev"
    __product_version__ = "0.0.0"
```

3. **Add to `.gitignore`:**
```
lawtime/_version.py
```

4. **Update `generate_version.py`:**
   - Remove `update_init_py()` function entirely
   - Add new `generate_version_py()` function that writes to `lawtime/_version.py`

5. **Untrack version_info.txt:**
```bash
git rm --cached version_info.txt
```

6. **Fix spec file path:**
   - Change `lawtime\\__main__.py` to `lawtime/__main__.py`

---

## Files You May Have That I Don't

Check for these potentially gitignored/local files that might affect the implementation:

- `venv/` - Virtual environment (may have different package versions)
- `dist/TimeLogger.exe` - Previous build output (check embedded version with file properties)
- `build/` - PyInstaller work directory
- Any `.env` or local config files
- `lawtime.db` - Database file (shouldn't affect this task)
- `%LOCALAPPDATA%\TimeLogger\` - Runtime data directory on Windows

---

## What NOT to Change

- `VERSION` file format - keep it simple `X.Y.Z`
- `TimeLogger.spec` structure (except the path fix)
- Build script flow (generate version → pyinstaller)
- The `version_info.txt` template format (PyInstaller requires specific structure)

---

## Testing the Fix

After implementation:

1. `git status` should be clean before AND after running build
2. Build twice consecutively - second build shouldn't show any git changes
3. Check `dist/TimeLogger.exe` → Right-click → Properties → Details → File version should show hash
4. Run the app - tray tooltip should show clean version like "TimeLogger v1.0.0"

---

## No Internet Research Needed

This is a straightforward refactoring task. PyInstaller version_info.txt format is already correctly implemented. The core issue is git hygiene, not PyInstaller configuration.

---

## Commits to Make

1. First commit: "Fix build script to not modify tracked files"
   - Add `lawtime/_version.py` to `.gitignore`
   - Modify `generate_version.py` to write `_version.py` instead of modifying `__init__.py`
   - Update `lawtime/__init__.py` with import fallback
   - Remove tracking of `version_info.txt`

2. Second commit: "Fix cross-platform path in PyInstaller spec"
   - Change backslash to forward slash in `TimeLogger.spec`
