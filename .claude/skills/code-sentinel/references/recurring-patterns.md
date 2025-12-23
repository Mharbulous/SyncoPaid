# Recurring Patterns Reference

This document catalogs recurring issues identified in the SyncoPaid codebase through analysis of 185 commits.

## CI/Workflow Patterns

### 1. Bash Heredocs in GitHub Actions YAML

**Issue:** Heredoc syntax fails due to indentation inside YAML `run:` blocks.

**Pattern to avoid:**
```yaml
run: |
  cat <<EOF > file.txt
  content here
  EOF
```

**Correct approach:**
```yaml
run: |
  VAR="line1"
  VAR="${VAR}\nline2"
  echo -e "$VAR" > file.txt
```

**Related commit:** d1394da - fix: replace heredoc with string assignment in workflow

---

### 2. Grep Exit Code Handling

**Issue:** `grep -c` returns exit code 1 when count is 0, causing `|| echo` to execute and create duplicate output.

**Pattern to avoid:**
```bash
count=$(grep -c pattern file || echo "0")
```

**Correct approach:**
```bash
count=$(grep -c pattern file || true)
```

**Related commit:** 4115ba9 - fix: correct task counting in verify-complexity step

---

### 3. Git Operations Without Staging

**Issue:** Git rebase/pull failing due to uncommitted changes.

**Pattern to avoid:**
```bash
git pull origin main
```

**Correct approach:**
```bash
# Option 1: Use autostash
git pull --rebase --autostash origin main

# Option 2: Stage files first
git add .
git pull --rebase origin main
```

**Related commit:** 5dd2b28 - fix(ci): stage files before rebase in decompose step

---

### 4. Non-Deterministic File Selection

**Issue:** File selection without secondary sort key leads to non-deterministic behavior.

**Pattern to avoid:**
```python
plans = sorted(plans, key=lambda x: x.priority)
```

**Correct approach:**
```python
plans = sorted(plans, key=lambda x: (x.priority, x.filename))
```

**Related commits:**
- dc6d1af - fix: remove duplicate plans and ensure deterministic plan selection
- 71e8761 - fix: update plan selection to handle hierarchical naming

---

## Application Patterns

### 5. Fixed Window Geometry

**Issue:** Fixed geometry (e.g., `400x200`) cutting off content when buttons/text don't fit.

**Pattern to avoid:**
```python
window = tk.Toplevel()
window.geometry("400x200")
```

**Correct approach:**
```python
window = tk.Toplevel()
# Let window auto-size to content
window.update_idletasks()
# Set minimum width only
window.minsize(400, 0)
```

**Related commit:** 216fce0 - fix: use auto-sizing for popup window height

---

### 6. PyInstaller Hidden Imports After Refactoring

**Issue:** When code is refactored into new modules, PyInstaller needs explicit hidden imports.

**Pattern to watch:**
- Refactoring large files into smaller modules
- Moving functions to new submodules

**Required action:**
```python
# In .spec file
hiddenimports=[
    'syncopaid.module',
    'syncopaid.submodule.new_file',  # Add after refactoring
]
```

**Related commit:** 68be291 - fix: add error reporting for tray open and fix PyInstaller bundling

---

### 7. Path Case Sensitivity

**Issue:** Path case mismatches can cause issues even on Windows when bundling.

**Pattern to avoid:**
```python
from MyModule import function  # Module is mymodule.py
```

**Correct approach:**
```python
from mymodule import function  # Match exact file case
```

**Related commit:** 68be291 - fix: add error reporting for tray open and fix PyInstaller bundling

---

### 8. Absolute Imports for Sibling Modules

**Issue:** Absolute imports for sibling modules within the syncopaid package fail in PyInstaller bundles because the module is not at the top-level namespace.

**Pattern to avoid:**
```python
# Inside src/syncopaid/context_extraction.py
from context_extraction_browser import extract_url_from_browser
```

**Correct approach:**
```python
# Use relative imports for sibling modules
from .context_extraction_browser import extract_url_from_browser
```

**Why it fails:** When running from source with `python -m syncopaid`, Python can resolve sibling modules. But PyInstaller bundles modules into a namespace hierarchy where bare module names like `context_extraction_browser` aren't found at the top level—they exist under `syncopaid.context_extraction_browser`.

**Related commit:** 2024964 - fix: use relative imports in context_extraction.py

---

## Statistics

From analysis of 185 commits:
- **CI/Workflow Issues:** 7 fixes (78%)
- **Application Issues:** 2-3 fixes (22%)

Most recurring issues are in the CI automation system rather than the SyncoPaid application itself.

## Story Re-execution Counts

Stories that required multiple re-executions due to issues:
- Story 8.1.1: Reset 7 times
- Story 8.1.2: Reset 7 times
- Story 1.7: Reset 4 times
- Story 9.5: Reset 3 times
- Story 8.2: Reset 3 times
- Story 4.6: Reset 3 times

These resets were primarily due to workflow system issues rather than application bugs.
