---
name: code-sentinel
description: Troubleshoot and fix failing code pattern tests. Use when tests/test_code_patterns.py fails, or when reviewing code changes that trigger recurring issue patterns. Automatically analyzes test failures, locates problematic code, suggests context-appropriate fixes, and verifies the solution works.
---

# Code Sentinel

Fix recurring anti-patterns detected by `tests/test_code_patterns.py`.

## Workflow

1. Run `pytest tests/test_code_patterns.py -v`
2. For each failing test, read the corresponding anti-pattern file
3. Apply the documented fix
4. Verify tests pass

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

Anti-pattern files are in `.claude/skills/code-sentinel/anti-patterns/`.
