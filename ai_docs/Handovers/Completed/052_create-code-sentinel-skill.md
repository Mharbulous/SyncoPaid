# Handover 052: Create Code-Sentinel Skill

## Objective
Create a custom skill named `code-sentinel` that remembers and checks for recurring errors in the SyncoPaid codebase.

## Context Completed
Just finished analyzing 185 commits to identify recurring issues. Created comprehensive report at:
```
ai_docs\Reports\2025-12-22-Recurring-Fixes.md
```

## Key Findings from Analysis

### Recurring Issue Categories (from report):

**1. CI Workflow: Plan Decomposition & Selection (78% of fixes)**
- c9c0f25, 71e8761, 8b22269, dc6d1af, d1394da, 4115ba9, 5dd2b28
- Issues: plan selection logic, hierarchical naming, git staging, task counting, bash heredoc syntax in YAML

**2. Popup/Dialog Window Sizing (22% of fixes)**
- 216fce0: Fixed geometry cutting off buttons → auto-sizing
- 2093517: Unclear popup text → improved UX

**3. PyInstaller Bundling (1 fix)**
- 68be291: Path case mismatch, missing hidden imports after refactoring

### Critical Patterns Identified

**Workflow Issues:**
- Git operations in CI with uncommitted changes
- Grep exit codes (`|| echo "0"` creates double output)
- Heredoc indentation in YAML fails
- Missing hidden imports after module refactoring
- Non-deterministic file selection without secondary sort

**Application Issues:**
- Fixed window geometry doesn't adapt to content
- PyInstaller needs explicit imports for refactored modules

## Next Task: Create code-sentinel Skill

### Skill Requirements
1. **Name:** `code-sentinel`
2. **Purpose:** Check code for known recurring issues before committing
3. **Scope:** Both application code AND CI/CD workflows

### Skill Should Check For:

**CI/Workflow Checks:**
- [ ] Bash heredocs in GitHub Actions YAML (suggest string concatenation)
- [ ] `grep -c || echo "0"` pattern (suggest `|| true`)
- [ ] Git operations without staging/autostash
- [ ] File selection without deterministic sorting
- [ ] Missing hidden imports in PyInstaller spec after refactoring

**Application Checks:**
- [ ] Fixed window geometry (suggest auto-sizing)
- [ ] Path case mismatches (Windows sensitivity)
- [ ] Missing error reporting in tray/GUI operations

### Implementation Approach

Use the `skill-creator` custom skill to generate the code-sentinel skill. The skill-creator is available in the environment.

**Skill invocation pattern:**
```
Use the Skill tool with skill="skill-creator"
```

### Key Files

**Report with full analysis:**
- `ai_docs\Reports\2025-12-22-Recurring-Fixes.md`

**PyInstaller spec (for import checks):**
- `SyncoPaid.spec` (contains hidden imports list)

**GitHub Actions workflow (for CI checks):**
- `.github\workflows\execute-stories.yml`

**Refactored modules (context for bundling issues):**
- `src\syncopaid\main_ui_windows.py`
- `src\syncopaid\tray_menu_handlers.py`
- Multiple refactored files in src\syncopaid\

### Red Herrings / Irrelevant Files
- Most feature implementation commits (not recurring issues)
- Story reset commits (these are workflow orchestration, not bugs)
- Refactor commits (planned improvements, not fixes)

### Technical Insights

**Bash in GitHub Actions:**
- Heredocs fail with indentation inside YAML `run:` blocks
- `grep -c` returns exit code 1 when count is 0, causing `|| echo` to execute and create duplicate output
- Always use `git pull --rebase --autostash` when files might be modified

**PyInstaller:**
- Hidden imports must be explicitly listed when code is refactored into new modules
- Path case matters even on Windows when bundling

**Tkinter Windows:**
- `.geometry("400x200")` is fragile
- Use auto-sizing with minimum width instead

## Branch Information
Working on: `claude/recurring-issues-analysis-othXP`
Latest commit: 913d003 (recurring issues report)

## Success Criteria
Code-sentinel skill should:
1. Be invocable via Claude Code skill system
2. Scan relevant files (CI YAML, Python source, spec files)
3. Provide actionable warnings for known recurring patterns
4. Reference specific commit IDs where issues occurred
5. Suggest fixes based on what worked previously
