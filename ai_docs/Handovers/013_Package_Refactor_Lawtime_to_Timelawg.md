# Handover 013: Package Refactoring - lawtime → src/timelawg

## What Was Done

Completed full package refactoring from `lawtime/` to `src/timelawg/` to:
1. Follow modern Python `src/` layout conventions (PEP 517/518)
2. Fix misleading package name (was backwards: "lawtime" instead of "timelawg")
3. Rename database from `lawtime.db` to `timelawg.db`

**Status**: Code changes complete, basic imports verified. Needs full Windows testing.

---

## Current State

### Package Structure (NEW)
```
TimeLawg/
├── src/
│   └── timelawg/              # Package (was lawtime/)
│       ├── __init__.py
│       ├── __main__.py        # Entry point
│       ├── config.py          # Has DB migration logic
│       ├── database.py
│       ├── tracker.py
│       ├── exporter.py
│       ├── screenshot.py
│       ├── action_screenshot.py
│       └── tray.py
├── pyproject.toml             # NEW - package config
├── generate_version.py        # Updated to output to src/timelawg/
├── TimeLawg.spec             # Updated entry point path
└── requirements.txt
```

### Key Changes Made

**Files Updated (All Import Statements)**:
- `src/timelawg/__init__.py` - line 10: `from timelawg._version`
- `src/timelawg/__main__.py` - lines 24-30, 34, 320: `from timelawg.*`
- `src/timelawg/tray.py` - line 25: `from timelawg import __product_version__`
- `src/timelawg/config.py` - lines 159, 175-183: DB filename + migration logic
- `generate_version.py` - line 202: Output path to `src/timelawg/_version.py`
- `TimeLawg.spec` - line 5: Entry point `src/timelawg/__main__.py`
- `launch_lawtime.bat` - line 4: `python -m timelawg`
- `create_shortcut.py` - line 32: `python -m timelawg` in bat template
- `test_screenshot_direct.py` - line 64: `from timelawg.screenshot`
- `diagnose_screenshots.py` - lines 74, 91, 110, 128, 145: `from timelawg.*`
- `README.md` - All commands, db references, directory structure
- `CLAUDE.md` - All commands, module structure, db path

**Files Created**:
- `pyproject.toml` - Modern package configuration with src/ layout

**Files Deleted**:
- `lawtime/` directory (entire old package)

---

## Critical Technical Details

### 1. Package Installation Required
The `src/` layout requires editable install:
```bash
pip install -e .
```
Without this, `python -m timelawg` fails with "No module named timelawg".

### 2. Database Migration (Automatic)
In `src/timelawg/config.py` lines 176-182:
```python
# Migration: rename old database if it exists
old_db = db_dir / 'lawtime.db'
new_db = db_dir / 'timelawg.db'
if old_db.exists() and not new_db.exists():
    logging.info(f"Migrating database from {old_db} to {new_db}")
    old_db.rename(new_db)
return new_db
```
First run automatically renames `lawtime.db` → `timelawg.db`. No manual migration needed.

### 3. Version Generation
`generate_version.py` creates `src/timelawg/_version.py` at build time (gitignored).
Fallback values in `__init__.py`: `"0.0.0.dev"` and `"0.0.0"`.

### 4. PyInstaller Entry Point
`TimeLawg.spec` line 5 now points to `src/timelawg/__main__.py` (forward slashes even on Windows).

---

## What Still Needs Testing (On Windows 11)

### Essential Tests
```bash
# 1. Module execution
python -m timelawg.tracker     # Should run 30s tracking test
python -m timelawg.database    # Should run DB tests
python -m timelawg.config      # Should show config info

# 2. Full application
python -m timelawg             # System tray should appear

# 3. Database migration
# If user has existing lawtime.db, verify it gets renamed to timelawg.db

# 4. Build process
python generate_version.py     # Should create src/timelawg/_version.py
pyinstaller TimeLawg.spec      # Should build dist/TimeLawg.exe
dist/TimeLawg.exe              # Should run without errors

# 5. Diagnostic scripts
python test_screenshot_direct.py
python diagnose_screenshots.py
```

### Verification Checklist
- [ ] Imports work without path hacks
- [ ] Database migration renames lawtime.db → timelawg.db on first run
- [ ] System tray icon launches
- [ ] Screenshots capture correctly
- [ ] Tracking records to database
- [ ] JSON export works
- [ ] PyInstaller build succeeds
- [ ] Built .exe runs on Windows 11

---

## Red Herrings / Ignore These

1. **Old `lawtime/` directory** - Deleted, don't look for it
2. **Test database names in exporter.py/database.py** - Still reference `test_lawtime.db` (harmless, just test fixtures)
3. **ai_docs/ references to lawtime** - Historical docs, don't need updating
4. **Windows path format confusion** - PyInstaller spec uses forward slashes even on Windows

---

## Key Source Files

### Must Read If Debugging
- `src/timelawg/config.py:154-183` - `_get_default_database_path()` with migration
- `pyproject.toml` - Package configuration for src/ layout
- `generate_version.py:202` - Version file output path
- `TimeLawg.spec:5` - PyInstaller entry point

### Documentation
- `C:\Users\Brahm\Git\TimeLawg\CLAUDE.md` - Development workflow (updated)
- `C:\Users\Brahm\Git\TimeLawg\README.md` - Installation guide (updated)

---

## Known Issues / Edge Cases

1. **Unicode print errors in generate_version.py** - Windows console encoding issue with ✓ character. Script still works, just prints ugly error.

2. **Module not found without pip install -e** - `src/` layout means Python can't find package without installation. This is CORRECT behavior for modern packages.

3. **User data path** - `%LOCALAPPDATA%\TimeLawg\` (note: folder is TimeLawg, db is timelawg.db)

---

## If Something Goes Wrong

### Rollback Plan
```bash
git checkout .                 # Restore all modified files
git clean -fd                  # Remove new files (pyproject.toml)
# Note: lawtime/ directory is already deleted from git history
```

### Common Issues

**"No module named timelawg"**
→ Run `pip install -e .` from project root

**PyInstaller can't find entry point**
→ Check `TimeLawg.spec` line 5 has `src/timelawg/__main__.py`

**Version import fails**
→ Run `python generate_version.py` to create `_version.py`

**Database not migrating**
→ Check `src/timelawg/config.py` lines 176-182 migration logic

---

## Next Steps

1. **Test on Windows 11** - Run verification checklist above
2. **Commit changes** - `git add . && git commit -m "Refactor: lawtime → src/timelawg following modern Python conventions"`
3. **Update .gitignore** - Ensure `src/timelawg/_version.py` is ignored
4. **Consider**: Rename `launch_lawtime.bat` to `launch_timelawg.bat` for consistency

---

## Context for Future Work

This was a structural refactoring with no functional changes. All features remain identical:
- Windows 11 time tracking
- Screenshot capture with dHash deduplication
- SQLite local storage
- JSON export for LLM processing
- System tray UI

The codebase is now positioned for modern Python packaging standards and potential PyPI distribution.
