# Anti-Pattern: Path Case Sensitivity

## Category
Application/Bundling

## Issue
Path case mismatches can cause issues even on Windows when bundling.

## Pattern to Avoid
```python
from MyModule import function  # Module is mymodule.py
```

## Correct Approach
```python
from mymodule import function  # Match exact file case
```

## Why It Fails
While Windows filesystem is case-insensitive, PyInstaller and other bundling tools may:
- Run on case-sensitive systems (Linux CI)
- Create case-sensitive archives
- Use case-sensitive module name mappings

This leads to "module not found" errors that only appear after bundling or in CI.

## Detection
Compare import statements against actual file names on disk, checking for case mismatches.

## Test Reference
No automated test (requires filesystem case comparison)

## Related Commit
68be291 - fix: add error reporting for tray open and fix PyInstaller bundling
