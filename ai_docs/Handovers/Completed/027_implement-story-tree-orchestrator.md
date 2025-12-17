# Implement Story Tree Orchestrator

## Task
Create `.github/workflows/story-tree-orchestrator.yml` based on v4 design.

## Design Spec (approved)
- `ai_docs/Plans/meta-workflow.json` - v4 spec with loop logic
- `ai_docs/Plans/meta-workflow.md` - v4 documentation

## Key Design Points

1. **Pipeline order**: plan-stories FIRST, then write-stories (drain before fill)
2. **Loop**: Shell while-loop in single job until `NO_APPROVED && NO_CAPACITY`
3. **Commit per cycle**: `git push` after each plan/write to preserve progress
4. **synthesize-goals**: NOT in loop - stays as separate daily workflow

## Reference Workflows
| File | Use |
|------|-----|
| `.github/workflows/plan-stories.yml` | Reference for Claude Code invocation pattern |
| `.github/workflows/write-stories.yml` | Reference for story_workflow.py usage |

## Scripts
| Script | Purpose |
|--------|---------|
| `.claude/scripts/story_workflow.py --ci` | Returns `NO_CAPACITY` when tree full |
| `.claude/scripts/insert_story.py` | Inserts generated story into DB |

## DB Query for Approved Count
```bash
sqlite3 .claude/story-tree.db "SELECT COUNT(*) FROM stories WHERE status='approved'"
```

## Loop Pseudo-code
```bash
while [ $cycle -lt $MAX_CYCLES ]; do
    # Plan if approved exists
    approved=$(sqlite3 .claude/story-tree.db "SELECT COUNT(*) FROM stories WHERE status='approved'")
    if [ "$approved" -gt 0 ]; then
        # invoke Claude Code with story-planning-ci skill
        git add -A && git commit -m "ci: plan story" && git push
        plan_result="SUCCESS"
    else
        plan_result="NO_APPROVED"
    fi

    # Write if capacity exists
    if ! python .claude/scripts/story_workflow.py --ci 2>&1 | grep -q "NO_CAPACITY"; then
        # invoke Claude Code to generate story
        python .claude/scripts/insert_story.py
        git add -A && git commit -m "ci: add story" && git push
        write_result="SUCCESS"
    else
        write_result="NO_CAPACITY"
    fi

    # Exit if idle
    [ "$plan_result" = "NO_APPROVED" ] && [ "$write_result" = "NO_CAPACITY" ] && break
    cycle=$((cycle + 1))
done
```

## Claude Code Action Pattern
From existing workflows:
```yaml
- name: Run Claude Code
  uses: anthropics/claude-code-action@beta
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    prompt: "..."
    allowed_tools: "Bash,Read,Write,Edit,Glob,Grep"
```

## NOT Relevant (ignore)
- `synthesize-goals-non-goals.yml` - separate workflow, not part of orchestrator
- Any v1-v3 design discussions - superseded by v4

## Branch
Push to: `claude/setup-github-actions-EFeMY` (or create PR from current branch)
