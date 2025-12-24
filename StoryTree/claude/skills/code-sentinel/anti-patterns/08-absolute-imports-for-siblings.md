# Anti-Pattern: Absolute Imports for Sibling Modules

## Category
Application/Bundling

## Issue
Absolute imports for sibling modules within the syncopaid package fail in PyInstaller bundles because the module is not at the top-level namespace.

## Pattern to Avoid
```python
# Inside src/syncopaid/context_extraction.py
from context_extraction_browser import extract_url_from_browser
```

## Correct Approach
```python
# Use relative imports for sibling modules
from .context_extraction_browser import extract_url_from_browser
```

## Why It Fails
When running from source with `python -m syncopaid`, Python can resolve sibling modules because:
1. The package directory is in `sys.path`
2. Python tries multiple import strategies

But PyInstaller bundles modules into a strict namespace hierarchy where bare module names like `context_extraction_browser` aren't found at the top level—they exist only under `syncopaid.context_extraction_browser`.

## Detection
Look for `from module_name import` (without leading dot) where `module_name` matches a file in `src/syncopaid/`.

## Test Reference
`tests/test_code_patterns.py::TestApplicationPatterns::test_sibling_imports_use_relative_syntax`

## Related Commit
2024964 - fix: use relative imports in context_extraction.py
