# Anti-Pattern: Git Operations Without Staging

## Category
CI/Workflow

## Issue
Git rebase/pull failing due to uncommitted changes.

## Pattern to Avoid
```bash
git pull origin main
```

## Correct Approach
```bash
# Option 1: Use autostash
git pull --rebase --autostash origin main

# Option 2: Stage files first
git add .
git pull --rebase origin main
```

## Why It Fails
In CI workflows that modify files before pulling/rebasing, uncommitted changes cause git operations to abort with an error about dirty working tree.

## Detection
Look for `git pull` or `git rebase` commands without `--autostash` flag and without a preceding `git add` within the same step.

## Test Reference
`tests/test_code_patterns.py::TestCIWorkflowPatterns::test_git_operations_with_staging`

## Related Commit
5dd2b28 - fix(ci): stage files before rebase in decompose step
