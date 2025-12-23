# Anti-Pattern: Grep Exit Code Handling

## Category
CI/Workflow

## Issue
`grep -c` returns exit code 1 when count is 0, causing `|| echo` to execute and create duplicate output.

## Pattern to Avoid
```bash
count=$(grep -c pattern file || echo "0")
```

## Correct Approach
```bash
count=$(grep -c pattern file || true)
```

## Why It Fails
When `grep -c` finds zero matches, it returns exit code 1 (not 0). The `|| echo "0"` then executes, but the original output (0) is also printed, resulting in duplicate or malformed output.

## Detection
Look for `grep -c` combined with `|| echo "0"` or `|| echo '0'` patterns.

## Test Reference
`tests/test_code_patterns.py::TestCIWorkflowPatterns::test_no_grep_exit_code_echo_pattern`

## Related Commit
4115ba9 - fix: correct task counting in verify-complexity step
