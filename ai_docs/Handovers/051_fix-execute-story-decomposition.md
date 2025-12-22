# Handover: Fix Execute-Story Workflow Decomposition

## Context

CI workflow `execute-stories.yml` fails intermittently when plans have 4+ TDD tasks. Root cause: the decompose job doesn't split plans aggressively enough.

**Branch:** `claude/debug-ci-workflow-0xZJs`

## The Problem

Decompose job (uses Opus) has wrong thresholds:
- Current: Only splits 7+ task plans into 3-5 task sub-plans
- Intended: Recursively split ALL plans until each has 1-2 tasks

A 6-task plan like `018_screenshot-categorization-ui.md` runs as-is, hits 50-turn limit, fails.

## Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/execute-stories.yml` | The workflow to fix (lines 1002-1015 for decompose prompt) |
| `.claude/skills/execute-story-workflow.md` | Documentation showing the flow with Mermaid diagram |
| `.claude/data/test-CI-runs/ExecuteStory#116.md` | Failed CI logs (287KB, use Grep to search) |

## Changes Required

### 1. Update decompose prompt (lines 1002-1015)

Replace complexity thresholds:
```yaml
## COMPLEXITY CLASSIFICATION
- simple: 1-2 tasks → execute directly
- complex: 3+ tasks → MUST decompose

## DECOMPOSITION RULES (MANDATORY)
If task_count > 2:
1. Split into sub-plans of 1-2 tasks each
2. Name: 016A_..., 016B_..., 016C_...
3. First sub-plan (A) executes this run
4. Remaining sub-plans queued for future runs

## AUTOMATIC COMPLEXITY ESCALATION
Always flag as complex (even if ≤2 tasks) when plan involves:
- GUI/UI testing (tkinter, Qt, browser)
- Image processing (PIL, OpenCV)
- System package dependencies
- External API calls
```

### 2. Add missing bash permissions (line 1286)

Add to `--allowedTools`:
```
Bash(source:*),Bash(cat:*),Bash(ls:*),Bash(rm:*),Bash(chmod:*)
```

### 3. Add Linux environment note to execute prompt

After line 1229 add:
```yaml
## ENVIRONMENT
- Runner: ubuntu-latest (Linux)
- Python venv: Use `source venv/bin/activate` NOT `venv\Scripts\activate`
- Use Linux paths with forward slashes
```

## Failure Analysis (from CI logs)

1. **Max-turns exceeded** (`"subtype": "error_max_turns"`, 50 turns)
2. **Permission denials:**
   - `venv\Scripts\activate` (Windows path on Linux)
   - `grep` bash command (should use Grep tool)
   - `apt-get install python3-tk` (not allowed)
3. Plan had 6 TDD tasks × 3 phases = 18+ operations, impossible in 50 turns

## Red Herrings

- Don't increase `--max-turns` significantly - fix decomposition instead
- The execute job model (Sonnet) is fine - problem is plan complexity not model capability
- Don't try to add `apt-get` permissions - plans shouldn't require system packages

## Commit & Push

After making changes, commit to branch `claude/debug-ci-workflow-0xZJs` and push.
