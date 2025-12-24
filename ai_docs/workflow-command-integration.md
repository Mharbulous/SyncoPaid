# Workflow Command Integration

This document shows how to integrate slash commands into the CI workflow.

## Current Approach (Inline Prompts)

```yaml
- name: "1.1 Review plan critically"
  uses: anthropics/claude-code-action@v1
  with:
    prompt: |
      You are reviewing a plan document...
      [60+ lines of prompt]
```

## New Approach (Slash Commands)

### Option A: Direct Command Invocation

```yaml
- name: "1.1 Review plan critically"
  uses: anthropics/claude-code-action@v1
  with:
    prompt: /ci-review-plan ${{ needs.setup-and-plan.outputs.plan_path }}
    claude_args: |
      --allowedTools "Read,Write,Edit,Glob,Grep,Bash(python:*),Bash(python3:*),Bash(mkdir:*)"
      --model claude-sonnet-4-5-20250929
      --max-turns 25
```

### Option B: Load and Expand (More Control)

```yaml
- name: "1.0.5 Prepare review prompt"
  id: prep-prompt
  run: |
    # Read command file and substitute variables
    PROMPT=$(cat .claude/commands/ci-review-plan.md)
    PROMPT="${PROMPT//\$ARGUMENTS/${{ needs.setup-and-plan.outputs.plan_path }}}"

    # Export for next step (handle multiline)
    {
      echo "REVIEW_PROMPT<<PROMPT_EOF"
      echo "$PROMPT"
      echo "PROMPT_EOF"
    } >> $GITHUB_ENV

- name: "1.1 Review plan critically"
  uses: anthropics/claude-code-action@v1
  with:
    prompt: ${{ env.REVIEW_PROMPT }}
```

## Benefits

| Aspect | Inline Prompts | Slash Commands |
|--------|---------------|----------------|
| **Workflow size** | 2292 lines | ~1500 lines |
| **Local testing** | Copy-paste prompt | `/ci-review-plan path/to/plan.md` |
| **Prompt iteration** | Edit YAML, commit, wait for CI | Edit .md, test locally |
| **Discoverability** | Hidden in YAML | Shows in `/` autocomplete |
| **Reusability** | None | Use in other workflows |

## Local Usage Examples

```bash
# Test review locally
claude "/ci-review-plan .claude/data/plans/024_feature.md"

# Test decomposition locally
claude "/ci-decompose-plan .claude/data/plans/024_feature.md"

# Debug why CI failed - run same command locally
claude "/ci-execute-plan .claude/data/plans/024A_first-step.md"
```

## Command Files Created

| Command | Purpose | Model (CI) |
|---------|---------|------------|
| `/ci-review-plan` | Critical review, decide outcome | Sonnet |
| `/ci-decompose-plan` | Assess complexity, split if needed | Opus |
| `/ci-identify-plan` | Match plan to database | Sonnet |
| `/ci-verify-implementation` | Check if implemented (TODO) | Sonnet |
| `/ci-execute-plan` | Follow TDD steps (TODO) | Sonnet |

## Migration Path

1. **Phase 1**: Extract prompts to commands (done for review, decompose)
2. **Phase 2**: Update workflow to use Option A (direct invocation)
3. **Phase 3**: Test locally to verify commands work
4. **Phase 4**: Remove inline prompts from workflow
