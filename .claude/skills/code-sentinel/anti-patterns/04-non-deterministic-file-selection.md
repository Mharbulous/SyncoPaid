# Anti-Pattern: Non-Deterministic File Selection

## Category
Code Quality

## Issue
File selection without secondary sort key leads to non-deterministic behavior.

## Pattern to Avoid
```python
plans = sorted(plans, key=lambda x: x.priority)
```

## Correct Approach
```python
plans = sorted(plans, key=lambda x: (x.priority, x.filename))
```

## Why It Fails
When multiple items have the same primary sort key (e.g., same priority), Python's sort is stable but the order depends on insertion order. If files are read from the filesystem, this order can vary between runs or platforms, causing flaky tests and unpredictable behavior.

## Detection
Look for `sorted()` calls with a single-value `key=lambda` that doesn't include a secondary sort criterion like filename or name.

## Test Reference
`tests/test_code_patterns.py::TestCodeQualityPatterns::test_deterministic_file_sorting`

## Related Commits
- dc6d1af - fix: remove duplicate plans and ensure deterministic plan selection
- 71e8761 - fix: update plan selection to handle hierarchical naming
