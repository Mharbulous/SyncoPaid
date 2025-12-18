# Handover: Add Token Usage Reporting to Remaining Workflows

## Task
Add token usage reporting (input_tokens, output_tokens, cache tokens, cost, duration) to these workflow files:
- `.github/workflows/plan-stories.yml`
- `.github/workflows/synthesize-goals-non-goals.yml`
- `.github/workflows/write-stories.yml`
- `.github/workflows/story-tree-orchestrator.yml`

## Completed Reference
`activate-stories.yml` already has the implementation - use it as the template.

Key changes made:
1. Added `id: claude` to the claude-code-action step
2. Added "Report Token Usage" step that parses `${{ steps.claude.outputs.execution_file }}`

## Workflow Categories

### Simple Pattern (plan-stories, synthesize-goals-non-goals, write-stories)
These use `anthropics/claude-code-action@v1`. Apply same pattern as activate-stories.yml:

```yaml
- name: Run Claude Code to ...
  id: claude  # ADD THIS
  uses: anthropics/claude-code-action@v1
  ...

- name: Report Token Usage  # ADD THIS STEP
  if: always()
  run: |
    # (copy from activate-stories.yml lines 212-257)
```

### Complex Pattern (story-tree-orchestrator.yml)
This uses `claude` CLI directly with `--output-format json` - NOT claude-code-action. It already parses some token data in the loop. The JSON output structure from CLI is:
```json
{"usage": {"input_tokens": N, "output_tokens": N}, "total_cost_usd": N.NN}
```

The orchestrator already logs to a progress table but could add aggregate totals to GITHUB_STEP_SUMMARY in the summary job.

## Execution File Format
The `execution_file` is JSONL. Grep for `"type":"result"` to find the final stats entry:
```json
{"type":"result", "usage":{"input_tokens":N,"output_tokens":N,"cache_creation_input_tokens":N,"cache_read_input_tokens":N}, "total_cost_usd":N.NN, "duration_ms":N}
```

## Key Sources
- [atlasfutures/claude-output-formatter](https://github.com/atlasfutures/claude-output-formatter) - Shows execution_file parsing pattern
- [anthropics/claude-code #1920](https://github.com/anthropics/claude-code/issues/1920) - Documents result event structure

## Branch
`claude/add-token-usage-reporting-Broo4`

## Commit Pattern
```bash
git add .github/workflows/<file> && git commit -m "feat: add token usage reporting to <workflow-name>"
git push -u origin claude/add-token-usage-reporting-Broo4
```
