# Anti-Pattern: PyInstaller Hidden Imports After Refactoring

## Category
Application/Bundling

## Issue
When code is refactored into new modules, PyInstaller needs explicit hidden imports.

## Pattern to Watch
- Refactoring large files into smaller modules
- Moving functions to new submodules
- Creating new deeply-nested module paths

## Required Action
```python
# In .spec file
hiddenimports=[
    'syncopaid.module',
    'syncopaid.submodule.new_file',  # Add after refactoring
]
```

## Why It Fails
PyInstaller performs static analysis to find imports. When modules are:
- Imported dynamically
- Referenced through string manipulation
- Deeply nested (2+ dots in path)

They may not be detected and must be explicitly listed.

## Detection
Look for `from syncopaid.x.y.z import` patterns (2+ dots) that aren't in the `.spec` file's `hiddenimports` list.

## Test Reference
`tests/test_code_patterns.py::TestApplicationPatterns::test_pyinstaller_hidden_imports`

## Related Commit
68be291 - fix: add error reporting for tray open and fix PyInstaller bundling
