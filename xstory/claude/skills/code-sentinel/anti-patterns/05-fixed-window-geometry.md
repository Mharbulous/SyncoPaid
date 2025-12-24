# Anti-Pattern: Fixed Window Geometry

## Category
Application/UI

## Issue
Fixed geometry (e.g., `400x200`) cutting off content when buttons/text don't fit.

## Pattern to Avoid
```python
window = tk.Toplevel()
window.geometry("400x200")
```

## Correct Approach
```python
window = tk.Toplevel()
# Let window auto-size to content
window.update_idletasks()
# Set minimum width only
window.minsize(400, 0)
```

## Why It Fails
Fixed window dimensions don't account for:
- Different font sizes across systems
- DPI scaling
- Dynamic content length
- Localization (translated text may be longer)

## Detection
Look for `.geometry("NNNxNNN")` patterns in Python files where both width and height are hardcoded.

## Test Reference
`tests/test_code_patterns.py::TestApplicationPatterns::test_no_fixed_window_geometry`

## Related Commit
216fce0 - fix: use auto-sizing for popup window height
