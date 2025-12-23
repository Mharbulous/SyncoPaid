---
name: code-sentinel
description: Troubleshoot and fix failing code pattern tests. Use when tests/test_code_patterns.py fails, or when reviewing code changes that trigger recurring issue patterns. Automatically analyzes test failures, locates problematic code, suggests context-appropriate fixes, and verifies the solution works.
---

# Code Sentinel

Intelligent troubleshooter for recurring code pattern failures.

## Overview

Code Sentinel helps fix recurring bugs by:
1. **Analyzing** failed test output from `test_code_patterns.py`
2. **Locating** the problematic code and understanding context
3. **Suggesting** appropriate fixes based on past solutions
4. **Applying** fixes with user approval
5. **Verifying** tests pass after fixes

## When to Use

Invoke this skill when:

1. **Pre-commit tests fail** - `pytest tests/test_code_patterns.py` shows failures
2. **CI build fails** - GitHub Actions reports code pattern violations
3. **Code review** - Checking changes against known problematic patterns
4. **Proactive fixing** - Addressing technical debt from old code

## Quick Start

When you see test failures like:

```bash
$ pytest tests/test_code_patterns.py -v

FAILED tests/test_code_patterns.py::TestApplicationPatterns::test_no_fixed_window_geometry
```

Simply invoke the skill:

```
/code-sentinel
```

Or provide specific context:

```
/code-sentinel - Fix the window geometry issue in settings_dialog.py
```

## Workflow

### Step 1: Understand the Failure

First, run the tests to see what failed:

```bash
pytest tests/test_code_patterns.py -v
```

Parse the output to identify:
- Which test failed
- What pattern was violated
- Where in the code (file:line)
- What the issue is

### Step 2: Analyze Context

Read the problematic file(s) to understand:
- The intent of the code
- Surrounding context
- Why the pattern was used
- What the code is trying to accomplish

### Step 3: Suggest Fix

Based on the pattern and context, suggest an appropriate fix. Each pattern has known good solutions (see references/recurring-patterns.md).

**Example patterns:**

| Pattern | Typical Fix |
|---------|-------------|
| Fixed window geometry | Replace with auto-sizing + minsize() |
| Heredoc in YAML | Use string concatenation |
| grep -c \|\| echo | Use \|\| true instead |
| git pull without autostash | Add --autostash flag |
| Missing hiddenimports | Add module to spec file |

### Step 4: Apply Fix

With user approval, apply the fix:
- Use Edit tool to modify the problematic code
- Follow the established pattern from past fixes
- Maintain code style and formatting

### Step 5: Verify

Re-run the specific test to verify:

```bash
pytest tests/test_code_patterns.py::TestName::test_name -v
```

If it passes, success! If not, analyze the failure and iterate.

### Step 6: Run Full Test Suite

Once the specific test passes, run all pattern tests:

```bash
pytest tests/test_code_patterns.py -v
```

Ensure no other tests were broken by the fix.

## Pattern Reference

### CI/Workflow Patterns (78% of historical fixes)

#### 1. Bash Heredocs in GitHub Actions

**Test:** `test_no_heredocs_in_github_actions`

**Issue:** Heredocs fail due to YAML indentation

**Fix Example:**
```yaml
# Bad
run: |
  cat <<EOF > file.txt
  content
  EOF

# Good
run: |
  CONTENT="line1"
  CONTENT="${CONTENT}\nline2"
  echo -e "$CONTENT" > file.txt
```

**Commit:** d1394da

---

#### 2. Grep Exit Code Pattern

**Test:** `test_no_grep_exit_code_echo_pattern`

**Issue:** `grep -c || echo "0"` creates duplicate output when count is 0

**Fix Example:**
```bash
# Bad
count=$(grep -c pattern file || echo "0")

# Good
count=$(grep -c pattern file || true)
```

**Commit:** 4115ba9

---

#### 3. Git Operations Without Staging

**Test:** `test_git_operations_with_staging`

**Issue:** git pull/rebase fails with uncommitted changes

**Fix Example:**
```yaml
# Bad
- run: git pull origin main

# Good - Option 1
- run: git pull --rebase --autostash origin main

# Good - Option 2
- run: |
    git add .
    git pull --rebase origin main
```

**Commit:** 5dd2b28

---

### Application Patterns (22% of historical fixes)

#### 4. Fixed Window Geometry

**Test:** `test_no_fixed_window_geometry`

**Issue:** Fixed geometry cuts off content when window needs more space

**Fix Example:**
```python
# Bad
window = tk.Toplevel()
window.geometry("400x200")

# Good
window = tk.Toplevel()
window.update_idletasks()  # Calculate natural size
window.minsize(400, 0)     # Set minimum width only
```

**Commit:** 216fce0

---

#### 5. PyInstaller Hidden Imports

**Test:** `test_pyinstaller_hidden_imports`

**Issue:** Refactored modules aren't bundled unless explicitly listed

**Fix Example:**
```python
# In *.spec file
a = Analysis(
    ...
    hiddenimports=[
        'syncopaid.existing_module',
        'syncopaid.ui.new_dialog',  # Add after refactoring
    ],
)
```

**Commit:** 68be291

---

## Advanced Usage

### Fix Specific Test

When you know which test failed:

```bash
# Run specific test
pytest tests/test_code_patterns.py::TestApplicationPatterns::test_no_fixed_window_geometry -v

# Then invoke skill with context
/code-sentinel - Fix the window geometry test failure
```

### Batch Fixing

When multiple tests fail:

1. Run all tests and collect failures
2. Prioritize by impact (CI/workflow > application)
3. Fix one at a time, verifying each
4. Re-run full suite after all fixes

### Understanding Test Output

Pytest output includes:
- **File:line** - Location of problematic code
- **Pattern** - What rule was violated
- **Fix suggestion** - How to address it
- **Commit reference** - Historical context

Use this information to quickly locate and fix issues.

## Integration with Development Workflow

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest tests/test_code_patterns.py --tb=short
if [ $? -ne 0 ]; then
    echo "Code pattern tests failed. Run /code-sentinel to fix."
    exit 1
fi
```

### CI/CD Pipeline

Already integrated in `.github/workflows/` - tests run on every PR.

### IDE Integration

Run tests in watch mode while developing:

```bash
pytest-watch tests/test_code_patterns.py
```

When failures appear, invoke `/code-sentinel` to fix them.

## Troubleshooting

### "Can't locate the issue"

If the skill can't find the problematic code:
1. Provide the full pytest output
2. Specify the file and line number
3. Show the relevant code snippet

### "Fix doesn't work"

If the suggested fix doesn't pass tests:
1. Check if there's additional context needed
2. Review the commit history for that pattern
3. Ensure the fix matches the specific use case

### "Multiple patterns in same file"

Fix one pattern at a time:
1. Start with the first test failure
2. Apply fix and verify
3. Move to next failure
4. This prevents conflicting changes

## Reference Materials

For detailed patterns and examples, see:

- **references/recurring-patterns.md** - All patterns with code examples and statistics

## Statistics

From analysis of 185 commits:
- **CI/workflow patterns:** 7 fixes (78%)
- **Application patterns:** 2-3 fixes (22%)

Most issues are in CI automation, not the core application.

## Limitations

This skill:
- ✅ Fixes known recurring patterns
- ✅ Understands context and intent
- ✅ Applies fixes based on past solutions
- ❌ Cannot fix novel bugs not in the pattern library
- ❌ Cannot validate business logic
- ❌ Cannot replace comprehensive testing

Always combine with:
- Manual code review
- Integration testing
- User acceptance testing
