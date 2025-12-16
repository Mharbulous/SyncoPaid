# Review Story Tree Orchestrator Workflow Logs

## Task
User ran the Story Tree Orchestrator workflow (max_cycles=1) and will paste the log output. Analyze for improvements.

## What Was Built
`.github/workflows/story-tree-orchestrator.yml` - v4 design implementing:
- **Gate job**: Checks `STORY_AUTOMATION_ENABLED` repo variable
- **drain-pipeline job**: Bash while-loop calling Claude CLI for plan→write
- **summary job**: Reports to `GITHUB_STEP_SUMMARY`

## Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/story-tree-orchestrator.yml` | The workflow being tested |
| `ai_docs/Plans/meta-workflow.json` | v4 design spec (authoritative) |
| `ai_docs/Plans/meta-workflow.md` | v4 documentation |
| `.claude/scripts/story_workflow.py` | Returns JSON context or `NO_CAPACITY` |
| `.claude/scripts/insert_story.py` | Inserts stories into DB |

## Branch
`claude/implement-story-tree-orchestrator-i4Oh2`

## Design Decisions Already Made
1. **Pipeline order**: plan-stories FIRST (drain), then write-stories (fill)
2. **Loop in single job**: Shell while-loop, not workflow_call or matrix
3. **Claude CLI**: Uses `@anthropic-ai/claude-code` npm package directly in bash loop
4. **Git per operation**: Commit+push after each plan/write to preserve progress
5. **Exit condition**: `NO_APPROVED && NO_CAPACITY` in same cycle = IDLE

## Known Unknowns (watch for in logs)
- Does Claude CLI work with `CLAUDE_CODE_OAUTH_TOKEN`? May need `ANTHROPIC_API_KEY` instead
- Does `--dangerously-skip-permissions` flag work in CI?
- Are the `--allowedTools` and `--model` flags correct syntax for CLI?
- Does the Skill invocation work from CLI prompt?

## What to Look For
1. **Authentication errors**: OAuth token vs API key
2. **CLI flag errors**: Wrong syntax for claude CLI
3. **Git conflicts**: Pull/push issues
4. **Skill execution**: Does `Skill(skill="story-planning-ci")` work from prompt?
5. **Loop logic**: Did it exit correctly based on conditions?
6. **Output parsing**: Did capacity check work?

## Existing Workflows (for reference)
- `.github/workflows/plan-stories.yml` - Uses `anthropics/claude-code-action@v1`
- `.github/workflows/write-stories.yml` - Uses `anthropics/claude-code-action@v1`

Note: These use the GitHub Action, not CLI directly. The orchestrator uses CLI to enable looping.
