---
name: code-sentinel
description: Use when tests/test_code_patterns.py fails - fixes recurring anti-patterns with documented root causes and verification
---

# Code Sentinel

Fix recurring anti-patterns detected by `tests/test_code_patterns.py`.

**You MUST use this skill when test_code_patterns.py fails.** Even if the fix looks obvious. The anti-pattern files document WHY patterns fail, not just HOW to fix them.

## Workflow

1. Run `pytest tests/test_code_patterns.py -v`
2. For each failing test, read the anti-pattern file (see mapping below)
3. Understand the root cause (not just the fix)
4. Apply the documented fix
5. Verify tests pass

## Test-to-File Mapping

| Test Name | Anti-Pattern File |
|-----------|-------------------|
| `test_no_heredocs_in_github_actions` | `01-heredocs-in-github-actions.md` |
| `test_no_grep_exit_code_echo_pattern` | `02-grep-exit-code-handling.md` |
| `test_git_operations_with_staging` | `03-git-operations-without-staging.md` |
| `test_deterministic_file_sorting` | `04-non-deterministic-file-selection.md` |
| `test_no_fixed_window_geometry` | `05-fixed-window-geometry.md` |
| `test_pyinstaller_hidden_imports` | `06-pyinstaller-hidden-imports.md` |
| (no automated test) | `07-path-case-sensitivity.md` |
| `test_sibling_imports_use_relative_syntax` | `08-absolute-imports-for-siblings.md` |

Anti-pattern files: `.claude/skills/code-sentinel/anti-patterns/`

## Common Mistakes

| Mistake | Why It's Wrong |
|---------|---------------|
| "Fix is obvious, skip the skill" | You miss the root cause. Next time you'll make the same mistake. |
| Fixing without reading anti-pattern doc | The doc explains WHY, not just WHAT. Understanding prevents recurrence. |
| Not verifying tests pass | The pattern might exist elsewhere in codebase. |
