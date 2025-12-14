# Building a Haiku-Optimized Git Specialist Agent for Claude Code

Claude Haiku 4.5 is ideal for git operations—**2x faster than Sonnet at one-third the cost**, with a 200K token context window and strong structured output capabilities. Git operations are deterministic, rule-based tasks that play to Haiku's strengths, making it the right choice for commit message generation, branch management, and deployment workflows. This guide provides production-ready patterns for your main→production promotion model.

## Haiku's sweet spot for git operations

Haiku excels at git automation because these tasks involve **structured inputs** (diffs, status), **deterministic rules** (conventional commits format), and **template-driven outputs**. Performance benchmarks show Haiku achieves 73.3% on SWE-bench versus Sonnet's 77.2%—a minimal gap for focused, well-defined tasks. The key constraint: keep individual operations simple, provide explicit templates, and avoid multi-step reasoning chains.

When to stick with Haiku: single-file commits, status checks, branch operations, log queries, and standard squash merges. Escalate to Sonnet for: merge conflict resolution involving complex logic, multi-file refactors requiring cross-codebase understanding, or security audits before production deployments.

## Production-ready system prompt for Haiku

This system prompt maximizes Haiku's performance through explicit rules, structured outputs, and clear examples:

```markdown
---
name: git-ops
description: Git operations specialist for commit management, branch workflows, and main→production promotion
tools: Bash, Read, Grep, Glob
model: haiku
---

You are a git operations specialist. Execute commands precisely and return structured results.

## Core Workflow: Main → Production Promotion
Development happens on main. When stable, squash merge main → production. GitHub Actions deploys from production.

## Pre-Operation Checklist (ALWAYS run first)
1. `git branch --show-current` - verify branch
2. `git status --porcelain` - check working tree clean
3. `git fetch origin` - sync remote state

## Commit Message Format
type(scope): imperative description under 50 chars

Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build
Rules:
- Imperative mood ("add" not "added")
- No period at end
- Lowercase type and description start
- Scope is optional, use affected component

Examples:
feat(auth): add OAuth2 login support
fix(api): prevent duplicate user creation
docs: update deployment runbook
refactor(db): extract connection pooling logic

## Squash Merge Message Template
For main→production promotion, use:

Deploy: [primary feature or fix summary]

Changes included:
- [key change 1]
- [key change 2]
- [key change 3]

Refs: [PR numbers or ticket IDs]

## Safety Rules
1. NEVER force push to main or production
2. NEVER run git reset --hard without confirmation
3. ALWAYS verify branch before destructive operations
4. ALWAYS run dry-run merge test before actual merge

## Output Format
Return JSON for all operations:
{
  "operation": "commit|merge|push|status",
  "status": "success|error|blocked",
  "branch": "current-branch",
  "details": "operation-specific information",
  "next_action": "suggested follow-up or null"
}

On error:
{
  "status": "error",
  "error_type": "merge_conflict|dirty_worktree|branch_mismatch|remote_rejected",
  "message": "human-readable description",
  "recovery_command": "git command to resolve"
}
```

## Commit message generation optimized for Haiku

Haiku generates excellent commit messages when given structured diff analysis. Use this two-phase approach to keep reasoning simple:

**Phase 1: Gather context (parallel execution)**
```bash
# Run these in parallel
git diff --staged --stat          # File change summary
git diff --staged                 # Actual changes  
git log --oneline -5              # Recent commit style reference
```

**Phase 2: Generate message with explicit template**

Prompt pattern for Haiku:
```
Analyze this staged diff and generate a conventional commit message.

Diff summary:
{diff_stat}

Diff content:
{diff_content}

Recent commits for style reference:
{recent_log}

Rules:
1. Identify primary change type (feat/fix/docs/refactor/test/chore)
2. Determine scope from file paths
3. Write imperative description under 50 chars
4. Add body only if change is non-obvious

Output exactly:
{"type": "...", "scope": "...", "subject": "...", "body": "..."}
```

**Real-world examples:**

Input diff showing new authentication endpoint:
```diff
+++ b/src/auth/oauth.ts
@@ -0,0 +1,45 @@
+export async function handleOAuthCallback(code: string) {
+  const token = await exchangeCodeForToken(code);
```

Output:
```json
{"type": "feat", "scope": "auth", "subject": "add OAuth callback handler", "body": "Implements token exchange flow for third-party authentication"}
```

Input diff showing bug fix:
```diff
--- a/src/api/users.ts
+++ b/src/api/users.ts
@@ -23,7 +23,8 @@ export async function createUser(data: UserInput) {
-  await db.users.insert(data);
+  const existing = await db.users.findByEmail(data.email);
+  if (!existing) await db.users.insert(data);
```

Output:
```json
{"type": "fix", "scope": "api", "subject": "prevent duplicate user creation", "body": "Checks for existing email before inserting new user record"}
```

## Main to production promotion workflow

This workflow implements your constraint: development on main, promotion via squash merge to production.

**Step-by-step promotion script:**
```bash
#!/usr/bin/env bash
set -Euo pipefail

# Error handling
trap 'echo "Error on line $LINENO: $BASH_COMMAND"; exit 1' ERR

MAIN_BRANCH="main"
PROD_BRANCH="production"

echo "=== Pre-flight checks ==="

# 1. Verify we're on main
CURRENT=$(git branch --show-current)
if [ "$CURRENT" != "$MAIN_BRANCH" ]; then
    echo "ERROR: Must run from $MAIN_BRANCH, currently on $CURRENT"
    exit 1
fi

# 2. Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: Working directory not clean"
    git status --short
    exit 1
fi

# 3. Sync with remote
git fetch origin

# 4. Ensure main is up to date
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$MAIN_BRANCH)
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "ERROR: Local $MAIN_BRANCH differs from remote"
    echo "Run: git pull origin $MAIN_BRANCH"
    exit 1
fi

# 5. Get commits to be promoted
COMMITS=$(git log origin/$PROD_BRANCH..HEAD --oneline)
if [ -z "$COMMITS" ]; then
    echo "No new commits to promote"
    exit 0
fi

echo "Commits to promote:"
echo "$COMMITS"

echo "=== Dry-run merge test ==="

# 6. Test merge without committing
git checkout $PROD_BRANCH
git pull origin $PROD_BRANCH

if ! git merge --no-commit --no-ff $MAIN_BRANCH 2>/dev/null; then
    echo "ERROR: Merge conflicts detected"
    git merge --abort
    git checkout $MAIN_BRANCH
    exit 1
fi
git merge --abort

echo "=== Executing squash merge ==="

# 7. Perform squash merge
git merge --squash $MAIN_BRANCH

# 8. Generate squash commit message
COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
FIRST_LINE=$(echo "$COMMITS" | head -1 | cut -d' ' -f2-)

# Create structured commit message
cat > /tmp/commit_msg.txt << EOF
Deploy: $FIRST_LINE

Squash merge of $COMMIT_COUNT commits from main:
$(echo "$COMMITS" | sed 's/^/- /')

Deployed: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

git commit -F /tmp/commit_msg.txt

# 9. Push to production (triggers GitHub Actions deployment)
git push origin $PROD_BRANCH

echo "=== Promotion complete ==="
git checkout $MAIN_BRANCH
echo "Production branch updated. GitHub Actions will deploy."
```

**Validation checklist for the agent:**

| Check | Command | Pass Condition |
|-------|---------|----------------|
| On correct branch | `git branch --show-current` | Returns "main" |
| Clean worktree | `git status --porcelain` | Empty output |
| Synced with remote | `git fetch && git diff HEAD origin/main` | Empty diff |
| No merge conflicts | `git merge --no-commit --no-ff production && git merge --abort` | Exit code 0 |
| CI passed | `gh pr checks` or GitHub API | All checks green |
| Production exists | `git rev-parse --verify production` | Exit code 0 |

## Token efficiency strategies for Haiku

Haiku has a **200K context window** but costs add up on large diffs. These tactics minimize tokens while maintaining quality:

**Diff optimization:**
```bash
# Instead of full diff, use stat for initial analysis
git diff --staged --stat --stat-width=80

# For large changes, sample key files
git diff --staged -- "*.ts" "*.tsx" | head -500

# Strip context lines for token savings
git diff --staged -U1  # Only 1 line of context vs default 3
```

**Prompt compression techniques:**
- Use abbreviations in system prompts: "conv commit" instead of "conventional commit format"
- Reference rules by number: "Follow rules 1-4" instead of restating them
- Use JSON output to avoid verbose prose
- Provide 2-3 examples, not 10—Haiku achieves near-Opus performance with just a few examples

**Batching operations:**
```bash
# Parallel tool calls in single request
git status --porcelain && git branch --show-current && git log -1 --oneline
```

**Cache system prompts:** Anthropic's prompt caching reduces cost for repeated identical prefixes. Store your git agent system prompt and cache it across invocations.

## Error handling patterns

Robust error handling keeps the agent from failing silently or making dangerous mistakes:

**Bash error template:**
```bash
#!/usr/bin/env bash
set -Euo pipefail

# Structured error output for agent parsing
error_json() {
    local type=$1 msg=$2 recovery=$3
    echo "{\"status\":\"error\",\"error_type\":\"$type\",\"message\":\"$msg\",\"recovery_command\":\"$recovery\"}"
    exit 1
}

# Pre-flight validation
validate_git_repo() {
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
        error_json "not_a_repo" "Not inside a git repository" "cd to repo directory"
}

validate_clean_worktree() {
    [ -z "$(git status --porcelain)" ] || \
        error_json "dirty_worktree" "Uncommitted changes present" "git stash or git commit"
}

validate_branch() {
    local expected=$1
    local current=$(git branch --show-current)
    [ "$current" = "$expected" ] || \
        error_json "wrong_branch" "Expected $expected, on $current" "git checkout $expected"
}

# Merge with conflict detection
safe_merge() {
    local source=$1
    if ! git merge --no-commit --no-ff "$source" 2>/dev/null; then
        git merge --abort
        error_json "merge_conflict" "Conflicts merging $source" "git diff to see conflicts"
    fi
    git merge --abort  # Clean up dry run
    git merge --squash "$source"
}
```

**Common failure modes and recoveries:**

| Error | Detection | Agent Response |
|-------|-----------|----------------|
| Merge conflict | Exit code != 0 on merge | Abort merge, report conflicting files, suggest manual resolution |
| Dirty worktree | `git status --porcelain` non-empty | List changed files, offer to stash or abort |
| Behind remote | `git log HEAD..origin/main` shows commits | Pull before proceeding |
| Push rejected | Exit code != 0 on push | Fetch and report divergence |
| Branch not found | `git rev-parse --verify` fails | List available branches |

## GitHub Actions integration verification

Ensure the agent can verify deployment status after promotion:

**Check workflow status:**
```bash
# Get latest workflow run for production branch
gh run list --branch production --limit 1 --json status,conclusion,displayTitle

# Wait for deployment to complete
gh run watch $(gh run list --branch production --limit 1 --json databaseId -q '.[0].databaseId')
```

**Deployment verification in workflow:**
```yaml
name: Deploy from Production
on:
  push:
    branches: [production]

jobs:
  verify-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Verify branch lineage
        run: |
          git fetch origin main
          if ! git merge-base --is-ancestor origin/main HEAD; then
            echo "::error::Production is not ahead of main"
            exit 1
          fi
          
      - name: Record deployment
        run: |
          echo "Deploying commit: $(git rev-parse --short HEAD)"
          echo "Commit message: $(git log -1 --format=%s)"
          
      - name: Deploy
        run: ./deploy.sh
```

**Agent can query deployment status:**
```bash
# Verify production includes main
git fetch origin
git merge-base --is-ancestor origin/main origin/production && \
    echo "Production up to date with main" || \
    echo "Production behind main - promotion needed"
```

## Testing your git agent

Validate agent behavior before production use:

**Unit test scenarios:**

1. **Commit message generation accuracy**
   - Feed known diffs, verify output matches expected format
   - Test edge cases: single-file changes, deletions only, renames

2. **Safety rule enforcement**
   - Attempt force push command—agent should refuse
   - Request operation on wrong branch—agent should error

3. **Error handling**
   - Create merge conflict scenario, verify graceful handling
   - Test with dirty worktree, verify appropriate error

**Integration test script:**
```bash
#!/bin/bash
# Create test repo
mkdir -p /tmp/test-repo && cd /tmp/test-repo
git init
git checkout -b main
echo "initial" > file.txt
git add . && git commit -m "initial commit"
git checkout -b production
git checkout main

# Test 1: Commit generation
echo "feature code" >> file.txt
git add file.txt
# Agent should generate: feat: add feature code (or similar)

# Test 2: Squash merge workflow
echo "more changes" >> file.txt
git add . && git commit -m "wip"
echo "final" >> file.txt  
git add . && git commit -m "done"
# Agent should squash these into production

# Test 3: Conflict detection
git checkout production
echo "conflicting" > file.txt
git add . && git commit -m "conflict source"
git checkout main
# Agent should detect conflict on promotion attempt

# Cleanup
rm -rf /tmp/test-repo
```

## Common pitfalls and how to avoid them

**Pitfall 1: Haiku generates verbose commit messages**
Solution: Explicitly request JSON output and specify character limits. Add "Output ONLY the JSON, no explanation" to prompts.

**Pitfall 2: Agent commits to wrong branch**
Solution: Make branch verification the FIRST step in every operation. Include branch name in output JSON for audit trail.

**Pitfall 3: Squash merge loses important context**
Solution: Template squash messages to list included commits. Store PR numbers in message for traceability.

**Pitfall 4: Agent doesn't detect partial failures**
Solution: Check exit codes explicitly. Git operations can "succeed" while printing warnings—capture stderr and analyze.

**Pitfall 5: Token budget exceeded on large diffs**
Solution: Implement diff truncation with priority: keep file headers, first 100 lines of each file, and deletion/addition counts for remainder.

## Complete agent file ready to deploy

Save this as `.claude/agents/git-ops.md`:

```markdown
---
name: git-ops
description: Git specialist for commits, squash merges, and main→production workflow. Invoke for any git operations, commit message drafting, or branch promotion.
tools: Bash, Read, Grep, Glob
model: haiku
---

You are a git operations specialist optimized for speed and precision.

## Workflow Context
- Development: main branch
- Promotion: squash merge main → production  
- Deployment: GitHub Actions triggers on production push

## Operations

### Draft Commit Message
1. Run: `git diff --staged --stat` and `git diff --staged`
2. Analyze change type from file patterns and diff content
3. Generate conventional commit: type(scope): description
4. Return: `{"message": "feat(scope): description", "body": "optional detail"}`

### Promote to Production
1. Verify on main: `git branch --show-current`
2. Verify clean: `git status --porcelain`
3. Sync: `git fetch origin`
4. Test merge: `git checkout production && git merge --no-commit --no-ff main && git merge --abort`
5. Execute: `git merge --squash main`
6. Commit with summary of changes
7. Push: `git push origin production`
8. Return to main: `git checkout main`

### Safety Rules
- NEVER force push to main or production
- NEVER proceed if worktree is dirty
- ALWAYS verify branch before operations
- ALWAYS test merge before executing

## Output Format (JSON)
Success: {"operation": "...", "status": "success", "branch": "...", "details": "..."}
Error: {"status": "error", "error_type": "...", "message": "...", "recovery_command": "..."}

## Commit Types
feat|fix|docs|style|refactor|test|chore|perf|ci|build

## Examples
feat(auth): add OAuth2 callback handler
fix(api): prevent duplicate user creation
chore(deps): upgrade typescript to 5.3
```

This agent configuration balances Haiku's strengths—speed, structured output, rule-following—against its limitations by keeping individual operations simple and providing explicit templates. The main→production workflow is fully supported with appropriate safety checks, and token efficiency is maintained through JSON outputs and focused prompts.