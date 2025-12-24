# Anti-Pattern: Bash Heredocs in GitHub Actions YAML

## Category
CI/Workflow

## Issue
Heredoc syntax fails due to indentation inside YAML `run:` blocks.

## Pattern to Avoid
```yaml
run: |
  cat <<EOF > file.txt
  content here
  EOF
```

## Correct Approach
```yaml
run: |
  VAR="line1"
  VAR="${VAR}\nline2"
  echo -e "$VAR" > file.txt
```

## Detection
Look for `<<EOF` or `<<'EOF'` patterns inside GitHub Actions YAML files within `run:` blocks.

## Test Reference
`tests/test_code_patterns.py::TestCIWorkflowPatterns::test_no_heredocs_in_github_actions`

## Related Commit
d1394da - fix: replace heredoc with string assignment in workflow
