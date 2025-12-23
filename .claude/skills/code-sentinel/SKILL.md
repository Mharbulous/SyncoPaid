---
name: code-sentinel
description: Check code for recurring issues before committing. Use when reviewing code changes, before git commits, during code review, or when implementing CI workflows, git operations, Tkinter UIs, or PyInstaller bundling. Detects patterns that have caused bugs in past commits including bash heredocs in YAML, grep exit codes, git operations without staging, fixed window geometry, and missing PyInstaller imports.
---

# Code Sentinel

Automated checker for recurring issues identified in the SyncoPaid codebase.

## Overview

Code Sentinel helps prevent recurring bugs by checking code against patterns that have caused issues in previous commits. Based on analysis of 185 commits, it focuses on the most common failure modes:

- **CI/Workflow Issues** (78% of recurring fixes)
- **Application Issues** (22% of recurring fixes)

## Quick Start

Run all checks on the entire codebase:

```bash
python .claude/skills/code-sentinel/scripts/check_all.py
```

Or run individual checks on specific files (see Checks section below).

## When to Use

Use Code Sentinel before committing changes, especially when:

1. **Modifying GitHub Actions workflows** - Check for heredocs and git operations
2. **Writing shell scripts** - Check for grep exit code handling
3. **Creating Tkinter windows** - Check for fixed geometry
4. **Refactoring Python modules** - Check PyInstaller hidden imports
5. **Implementing file selection logic** - Check for deterministic sorting

## Checks

### 1. Bash Heredocs in GitHub Actions YAML

**Script:** `check_heredoc_yaml.py`

**Usage:**
```bash
python .claude/skills/code-sentinel/scripts/check_heredoc_yaml.py .github/workflows/workflow.yml
```

**What it detects:** Heredoc syntax (`<<EOF`) inside YAML `run:` blocks, which fails due to indentation.

**Fix:** Use string concatenation instead of heredocs.

**Related commit:** d1394da

---

### 2. Grep Exit Code Issues

**Script:** `check_grep_exit_code.py`

**Usage:**
```bash
python .claude/skills/code-sentinel/scripts/check_grep_exit_code.py script.sh
```

**What it detects:** `grep -c || echo "0"` pattern that creates duplicate output when count is 0.

**Fix:** Use `|| true` instead of `|| echo "0"`.

**Related commit:** 4115ba9

---

### 3. Git Operations Without Staging

**Script:** `check_git_operations.py`

**Usage:**
```bash
python .claude/skills/code-sentinel/scripts/check_git_operations.py .github/workflows/workflow.yml
```

**What it detects:** `git pull` or `git rebase` without `--autostash` or preceding `git add`.

**Fix:** Use `git pull --rebase --autostash` or stage files first.

**Related commit:** 5dd2b28

---

### 4. Fixed Window Geometry

**Script:** `check_window_geometry.py`

**Usage:**
```bash
python .claude/skills/code-sentinel/scripts/check_window_geometry.py src/syncopaid/ui.py
```

**What it detects:** Fixed Tkinter geometry like `.geometry("400x200")` that may cut off content.

**Fix:** Use auto-sizing with `update_idletasks()` and set minimum width only.

**Related commit:** 216fce0

---

### 5. PyInstaller Hidden Imports

**Script:** `check_pyinstaller_imports.py`

**Usage:**
```bash
python .claude/skills/code-sentinel/scripts/check_pyinstaller_imports.py SyncoPaid.spec src/
```

**What it detects:** Modules imported in source code that may be missing from PyInstaller `hiddenimports` list, especially after refactoring.

**Fix:** Add missing modules to `hiddenimports` in the .spec file.

**Related commit:** 68be291

---

## Workflow Integration

### Before Committing

```bash
# Run all checks
python .claude/skills/code-sentinel/scripts/check_all.py

# If issues found, review and fix
# Then commit
git add .
git commit -m "fix: address code-sentinel findings"
```

### In CI/CD Pipeline

Add to GitHub Actions workflow:

```yaml
- name: Run Code Sentinel checks
  run: |
    python .claude/skills/code-sentinel/scripts/check_all.py
```

### During Code Review

Run targeted checks based on file types:

```bash
# For workflow changes
python .claude/skills/code-sentinel/scripts/check_heredoc_yaml.py .github/workflows/*.yml

# For Python changes
python .claude/skills/code-sentinel/scripts/check_window_geometry.py src/**/*.py
python .claude/skills/code-sentinel/scripts/check_pyinstaller_imports.py *.spec src/
```

## Interpreting Results

Each check script returns:
- **Exit code 0:** No issues found
- **Exit code 1:** Issues detected

When issues are found, the output includes:
- Line number where issue occurs
- Content of the problematic line
- Explanation of why it's an issue
- Suggested fix
- Related commit ID for reference

Example output:
```
⚠️  Found 1 heredoc issue(s) in .github/workflows/ci.yml:

  Line 42: Bash heredoc detected in YAML run block
    Content: cat <<EOF > output.txt
    Suggestion: Use string concatenation instead: VAR="value1"\nVAR="${VAR}value2"
    Related commit: d1394da
```

## Reference Material

For detailed examples and historical context, see:

- **references/recurring-patterns.md** - Detailed patterns with code examples and statistics

## Limitations

Code Sentinel checks for known patterns only. It does not:
- Catch all possible bugs
- Replace code review
- Test functionality
- Validate logic correctness

Always combine with:
- Manual code review
- Automated tests
- Integration testing
- Linter/formatter tools

## Statistics

From analysis of 185 commits in the SyncoPaid repository:
- 7 CI/workflow pattern fixes (78%)
- 2-3 application pattern fixes (22%)

Most recurring issues are in the CI automation system rather than the application itself, which shows healthy development patterns with minimal recurring bugs in core functionality.
