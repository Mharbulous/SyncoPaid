# Token Efficiency Guide for Custom Skills, Workflows, and GitHub Actions

This guide consolidates lessons learned from optimizing token usage across custom skills, slash commands, and GitHub workflow actions in the SyncoPaid project. Total documented savings: **~3,800+ tokens per workflow run**.

## Quick Reference: Token Savings by Optimization Type

### Validated Optimizations (Parts 1-5)

| Optimization | Token Savings | Complexity |
|--------------|---------------|------------|
| Remove redundant CLAUDE.md read | ~400 tokens | Low |
| Combine file checks into single script | ~200 tokens | Low |
| Add CI mode minimal output | ~500 tokens | Low |
| Consolidate SQL queries | ~400 tokens | Medium |
| Batch skill invocations | ~1,400 tokens | Medium |
| Optimize CLAUDE.md structure | ~1,000+ tokens | High |

### Theoretical Optimizations (Part 6 - Untested)

| Optimization | Claimed Savings | Complexity |
|--------------|-----------------|------------|
| Token-efficient API beta | Variable | Low |
| Dynamic tool loading | 85% | High |
| MCP server auditing | 50-90% | Low |
| Haiku model routing | 70% cost | Medium |
| Strategic /compact | Quality | Low |
| Explore subagent isolation | Context isolation | Low |
| 75% utilization target | Quality | Low |
| /clear between tasks | 50-70% | Medium |

> See [Part 6](#part-6-theoretical-optimizations-untested) for implementation details and testing requirements.

---

## Part 1: Skill Optimization Patterns

### 1.1 Avoid Redundant File Reads

**Anti-pattern: Instructing skills to read CLAUDE.md**

```yaml
# BAD - Workflow prompt
1. Read CLAUDE.md for project conventions
2. Execute the /write-stories command...
```

CLAUDE.md is automatically loaded into the `claudeMd` system context on every conversation. Explicitly instructing Claude to read it wastes ~400 tokens per invocation.

**Fix: Remove redundant read instructions**

```yaml
# GOOD - Workflow prompt
1. Execute the /write-stories command which will:
   - Query the story-tree database...
```

### 1.2 Combine File Operations into Single Scripts

**Anti-pattern: Sequential file checks**

```python
# BAD - Two separate operations (~400 tokens with tool overhead)
# Step 1: Check existence
python -c "
import os
vision_path = 'ai_docs/user-vision.md'
anti_vision_path = 'ai_docs/user-anti-vision.md'
has_vision = os.path.exists(vision_path)
has_anti_vision = os.path.exists(anti_vision_path)
print(f'Vision file exists: {has_vision}')
print(f'Anti-vision file exists: {has_anti_vision}')
"

# Step 2: If exists, read file (another tool call)
```

**Fix: Single script that checks and reads**

```python
# GOOD - One operation, returns all needed data (~200 tokens saved)
python -c "
import os, json
result = {'vision': None, 'anti_vision': None, 'has_vision': False, 'has_anti_vision': False}
for key, path in [('vision', 'ai_docs/user-vision.md'), ('anti_vision', 'ai_docs/user-anti-vision.md')]:
    if os.path.exists(path):
        result[f'has_{key}'] = True
        with open(path) as f:
            result[key] = f.read()
print(json.dumps(result, indent=2))
"
```

**Key principle:** Each tool invocation has overhead. Combine related operations into single JSON-returning scripts.

### 1.3 Consolidate SQL Queries

**Anti-pattern: Multiple database queries for related data**

```python
# BAD - Step 1: Query capacity nodes
cursor.execute('SELECT ... FROM stories WHERE capacity < max ...')
nodes = cursor.fetchall()

# BAD - Step 2: Separate query for refine nodes
cursor.execute('SELECT ... FROM stories WHERE status = "refine" ...')
refine_nodes = cursor.fetchall()
```

**Fix: Single query returning all needed data**

```python
# GOOD - One database call returns structured result
result = {'capacity_nodes': [], 'refine_nodes': []}

# Query 1: capacity nodes
cursor.execute('SELECT ... WHERE capacity < max ... LIMIT 2')
result['capacity_nodes'] = [dict(row) for row in cursor.fetchall()]

# Query 2: refine nodes (same connection)
cursor.execute('SELECT ... WHERE status = "refine" ... LIMIT 3')
result['refine_nodes'] = [dict(row) for row in cursor.fetchall()]

print(json.dumps(result, indent=2))
```

**Savings:** ~400 tokens by eliminating tool invocation overhead between queries.

### 1.4 Batch Skill Invocations

**Anti-pattern: Invoking skills once per item**

```markdown
# BAD - Calls skill N times
For each node found in Step 1:
1. Use the Skill tool to invoke `brainstorm-story`
2. Pass the node ID and request stories be generated
```

This loads the full skill document (~2,800 tokens) for each invocation.

**Fix: Design skills to accept multiple inputs**

```markdown
# GOOD - Single skill call with all targets
If `capacity_nodes` from Step 1 contains any nodes:
1. Use the Skill tool to invoke `brainstorm-story`
2. Pass ALL discovered node IDs together (e.g., "Generate stories for nodes: 1.2, 1.3")
3. Request 1 story per node, max 2 stories total
```

**Skill-side implementation:**

```markdown
## Multi-Node Batching (CI Optimization)

When called with multiple node IDs (e.g., "Generate stories for nodes: 1.2, 1.3"):

1. **Parse all node IDs** from the instruction
2. **Perform Steps 0-2 once** (vision check, git analysis) - shared context
3. **Loop through nodes for Steps 3-6**: For each node, run context gathering
4. **Output single combined report** covering all nodes

**Token savings:** Processing N nodes in one invocation avoids loading skill
document N times, saving ~2,800 tokens per additional node.
```

**Savings:** ~1,400 tokens per additional node in batch.

### 1.5 Add CI Mode for Minimal Output

**Anti-pattern: Verbose output in automated contexts**

Interactive sessions benefit from detailed reports, but GitHub Actions runs don't need them.

```markdown
# BAD - Same verbose output regardless of context
### Step 7: Report Results

Present findings in detailed report format:
- Executive summary
- Node analysis with evidence
- Story recommendations
- Next steps discussion
```

**Fix: Detect CI context and use minimal format**

```markdown
### Step 7 (CI Mode): Minimal Output

**When running in CI/automation context** (e.g., scheduled GitHub Actions):

**Single node:**
```
✓ Generated [N] stories for node [PARENT_ID]:
  - [STORY_ID_1]: [Title 1]
  - [STORY_ID_2]: [Title 2]
```

**Multi-node batch:**
```
✓ Generated [N] stories across [M] nodes:
  [NODE_1]: [STORY_ID_1] - [Title 1]
  [NODE_2]: [STORY_ID_2] - [Title 2]
```

**CI mode indicators:**
- Running via GitHub Actions workflow
- Called by command in autonomous mode
- No interactive user session

**Benefits:** Reduces token usage by ~500 tokens per invocation.
```

---

## Part 2: GitHub Workflow Action Optimization

### 2.1 Prompt Engineering for Token Efficiency

**Anti-pattern: Verbose, redundant instructions**

```yaml
prompt: |
  You are a helpful assistant running in GitHub Actions.
  Please read the CLAUDE.md file to understand the project.
  Then run the /write-stories command.
  After that, please commit any changes.
  Make sure to push the changes to the repository.
```

**Fix: Structured, minimal prompts**

```yaml
prompt: |
  REPO: ${{ github.repository }}
  MODE: Daily Story Generation (YOLO mode - fully autonomous)

  ## Primary Task: Generate User Stories
  Run the /write-stories slash command to generate new user story concepts.

  Key behaviors for YOLO mode:
  - Skip all approval steps - do NOT wait for user confirmation
  - Generate up to 2 stories for nodes with capacity
  - Create commits directly with clear messages
  - No interactive prompts - complete autonomously

  ## Workflow Steps:
  1. Execute the /write-stories command which will:
     - Query the story-tree database for nodes with capacity
     - Use the brainstorm-story skill to generate stories
     - Insert new concept stories into the database
  2. Commit and push any changes
```

### 2.2 Restrict Tools to Reduce Context

**Anti-pattern: Allowing all tools**

```yaml
# BAD - Loads documentation for unused tools
claude_args: |
  --allowedTools "*"
```

**Fix: Whitelist only needed tools**

```yaml
# GOOD - Only loads relevant tool documentation
claude_args: |
  --allowedTools "Task,Read,Write,Edit,Glob,Grep,Bash(git:*),Bash(python:*),Bash(python3:*),Bash(sqlite3:*),Skill,SlashCommand,TodoWrite"
```

### 2.3 Avoid Unnecessary Git Operations

**Anti-pattern: Complex branching in simple automation**

```yaml
prompt: |
  1. Create a new branch for changes
  2. Make changes
  3. Commit to branch
  4. Create PR
  5. Wait for approval
```

**Fix: Direct commits for automation**

```yaml
prompt: |
  ## Git Operations (REQUIRED for ANY file changes):
  1. Ensure you are on main branch and pull latest:
     ```bash
     git checkout main
     git pull origin main
     ```
  2. Stage and commit all changes:
     ```bash
     git add -A
     git commit -m "stories: auto-generate concept stories $(date -u +'%Y-%m-%d')"
     ```
  3. Push directly to main:
     ```bash
     git push origin main
     ```
```

---

## Part 3: CLAUDE.md Optimization

### 3.1 Keep Root File Under 100 Lines

CLAUDE.md is loaded on every conversation. Bloated files waste tokens constantly.

**Anti-pattern: Everything in one file**
- 200+ lines of detailed documentation
- API references
- Configuration tables
- Detailed class descriptions

**Fix: Progressive disclosure**

```markdown
# CLAUDE.md (optimized)

## Critical Rules
- **YOU MUST** activate virtual environment
- **ALWAYS** use native Windows paths

## Project Summary
Brief 2-3 sentence description.

## Commands
Essential commands only.

## Architecture
High-level diagram.

## Reference
For detailed config, APIs, classes, see `ai_docs/technical-reference.md`.
```

Move detailed content to separate files that Claude reads on-demand.

### 3.2 Use Tables for Dense Information

**Anti-pattern: Prose descriptions**

```markdown
The database file is stored at %LOCALAPPDATA%\SyncoPaid\SyncoPaid.db.
The config file is at %LOCALAPPDATA%\SyncoPaid\config.json.
Screenshots are saved to %LOCALAPPDATA%\SyncoPaid\screenshots\YYYY-MM-DD\.
```

**Fix: Structured tables**

```markdown
| File | Path |
|------|------|
| Database | `%LOCALAPPDATA%\SyncoPaid\SyncoPaid.db` |
| Config | `%LOCALAPPDATA%\SyncoPaid\config.json` |
| Screenshots | `%LOCALAPPDATA%\SyncoPaid\screenshots\YYYY-MM-DD\` |
```

Tables convey the same information in ~40% fewer tokens.

### 3.3 Use Abbreviations and Shorthand

**Anti-pattern: Full sentences**

```markdown
The TrackerLoop class polls the active window information.
The ScreenshotWorker class performs asynchronous screenshot capture.
```

**Fix: Terse annotations**

```markdown
├── tracker.py     # TrackerLoop: polls active window, yields ActivityEvent
├── screenshot.py  # ScreenshotWorker: async capture with dHash deduplication
```

---

## Part 4: Anti-Patterns Checklist

Use this checklist to identify token waste in your skills and workflows:

### Skill Anti-Patterns

- [ ] **Redundant file reads** - Instructions to read files already in context
- [ ] **Sequential file checks** - Checking existence, then reading in separate calls
- [ ] **Multiple database queries** - Separate queries for related data
- [ ] **Per-item skill calls** - Invoking skills in loops instead of batching
- [ ] **Verbose output in CI** - Full reports when running automated
- [ ] **Unnecessary context loading** - Loading files/data not needed for task

### Workflow Anti-Patterns

- [ ] **Read CLAUDE.md instruction** - Already available in claudeMd context
- [ ] **Unrestricted tools** - Using `--allowedTools "*"` instead of whitelist
- [ ] **Verbose prompts** - Long explanations instead of structured steps
- [ ] **Complex git workflows** - Creating branches/PRs for simple automation
- [ ] **Missing CI mode** - No minimal output format for automated runs

### CLAUDE.md Anti-Patterns

- [ ] **File over 100 lines** - Should use progressive disclosure
- [ ] **Detailed API references** - Move to separate reference doc
- [ ] **Prose over tables** - Use tables for structured data
- [ ] **Redundant information** - Same info stated multiple ways
- [ ] **Implementation details** - Move class docs to technical reference

---

## Part 5: Implementation Checklist

When optimizing an existing skill or workflow:

1. **Measure baseline** - Count approximate tokens in current version
2. **Check for redundant reads** - Remove CLAUDE.md and duplicate file reads
3. **Consolidate operations** - Combine file checks, SQL queries into single scripts
4. **Add batching support** - Design skills to accept multiple inputs
5. **Add CI mode** - Create minimal output format for automated contexts
6. **Restrict tools** - Whitelist only necessary tools in workflow actions
7. **Measure improvement** - Estimate token savings from changes

---

## Appendix: Commits Referenced

| Commit | Description | Savings |
|--------|-------------|---------|
| `337e746` | Phase 1 token efficiency optimizations | ~1,100 tokens |
| `c0955ca` | Phase 2 token efficiency optimizations | ~1,800 tokens |
| `b85fa50` | Plan-story workflow optimizations | ~900 tokens |
| `c97a8ed` | CLAUDE.md optimization and restructure | ~1,000+ tokens |
| `2c0695e` | GitHub workflow configuration improvements | Variable |

---

## Summary

The most impactful optimizations are:

1. **Remove redundant CLAUDE.md reads** (~400 tokens/workflow)
2. **Batch skill invocations** (~1,400 tokens/additional node)
3. **Add CI mode output** (~500 tokens/invocation)
4. **Consolidate SQL/file operations** (~200-400 tokens/optimization)
5. **Keep CLAUDE.md lean** (~1,000+ tokens/session)

Focus on batching and CI mode for the highest ROI. These changes compound across every automated run.

---

## Part 6: Theoretical Optimizations (Untested)

> **IMPORTANT:** The strategies in this section are derived from internet research and external sources. They have NOT been validated through practical testing on the SyncoPaid repository. These suggestions should remain in this theoretical section until they have been tested and confirmed to provide measurable benefits in this specific codebase.
>
> **To promote a strategy to the validated sections above:**
> 1. Implement the optimization in a test workflow or skill
> 2. Measure baseline token usage before optimization
> 3. Measure token usage after optimization
> 4. Document the actual savings in a commit
> 5. Move the strategy to the appropriate validated section

---

### 6.1 Token-Efficient Tool Use API Beta

**Source:** [Claude Docs - Token-efficient tool use](https://docs.claude.com/en/docs/agents-and-tools/tool-use/token-efficient-tool-use)

**Claimed benefit:** Reduces input and output tokens for tool use requests.

**Implementation:**
```python
# Add beta header to API requests
headers = {
    "anthropic-beta": "token-efficient-tools-2025-02-19"
}
```

**Expected savings:** Variable (Anthropic states "on average uses fewer tokens")

**Testing needed:** Enable beta header in GitHub Actions workflow, compare token usage across multiple runs.

---

### 6.2 Dynamic Tool Loading / Tool Search

**Source:** [Anthropic - Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)

**Claimed benefit:** 85% reduction in token usage for tool definitions.

**How it works:**
- Instead of loading all tool definitions upfront, use `defer_loading: true`
- Claude discovers tools on-demand via Tool Search Tool
- Only needed tools are loaded into context

**Implementation:**
```json
{
  "tools": [
    {
      "name": "my_tool",
      "defer_loading": true,
      "description": "Tool description for search matching"
    }
  ]
}
```

**Expected savings:** 85% reduction in tool definition tokens (from ~55K to ~8K for 58 tools)

**Testing needed:** Requires API-level changes; may not be applicable to Claude Code CLI directly. Investigate if `--allowedTools` already provides similar benefits.

---

### 6.3 MCP Server Token Auditing

**Source:** [Scott Spence - Optimising MCP Server Context Usage](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)

**Claimed benefit:** 50-90% token reduction by disabling unused MCP servers.

**Problem:** MCP servers can consume 66,000+ tokens before conversation starts. A five-server setup with 58 tools consumes ~55K tokens of context overhead.

**Implementation:**
```bash
# Audit current MCP usage
/context

# Disable unused servers
@server-name disable
# or use /mcp menu

# Set output limits
export MAX_MCP_OUTPUT_TOKENS=25000
```

**Expected savings:** 50-90% depending on number of MCP servers in use

**Testing needed:** Run `/context` in current setup to audit MCP token consumption. This project may not use MCP servers extensively.

---

### 6.4 Haiku Model Routing for Subagents

**Source:** [Anthropic - Claude Haiku 4.5](https://www.anthropic.com/claude/haiku), [Claude Code Subagents Docs](https://code.claude.com/docs/en/sub-agents)

**Claimed benefit:** 70% cost reduction, 90% of Sonnet performance.

**How it works:**
- Use Haiku for simple, repetitive tasks
- Reserve Sonnet/Opus for complex reasoning
- Subagents automatically isolate context

**Implementation in skills:**
```markdown
## Skill Frontmatter
model: haiku  # For simple data gathering tasks
```

**Implementation in Task tool:**
```yaml
# In workflow or slash command
Use the Task tool with:
  - subagent_type: Explore
  - model: haiku
```

**Expected savings:** 70% cost reduction (Haiku: $1/$5 vs Sonnet: $3/$15 per million tokens)

**Testing needed:** Modify brainstorm-story or similar skill to use Haiku for data gathering steps, measure quality vs cost trade-off.

---

### 6.5 Strategic /compact at Task Boundaries

**Source:** [ClaudeLog - Auto-Compact](https://claudelog.com/faqs/what-is-claude-code-auto-compact/)

**Claimed benefit:** Preserves context quality by compacting at logical boundaries.

**Problem:** Auto-compact triggers at ~95% context, often mid-task. Manual compaction at 85-90% or at task completion produces better summaries.

**Implementation for GitHub Actions:**
```yaml
prompt: |
  ## After completing primary task:
  1. Run `/compact preserve the implementation decisions and file changes made`
  2. Then proceed to next task phase
```

**Implementation for skills:**
```markdown
### Step N: Context Checkpoint
If conversation has exceeded 50 messages or is approaching context limits:
1. Run /compact with focus: "preserve {specific context}"
2. Continue to next step
```

**Expected savings:** Quality preservation (prevents degraded reasoning from context rot)

**Testing needed:** Add /compact calls to visualization workflow at step boundaries, measure output quality before/after.

---

### 6.6 Prompt Caching for Repeated System Context

**Source:** Anthropic API documentation

**Claimed benefit:** 90% cost reduction on cached tokens.

**How it works:**
- Mark static prompt portions with `cache_control: {"type": "ephemeral"}`
- First request caches, subsequent requests hit cache
- 5-minute TTL, refreshes on use

**Implementation:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Large static context here...",
          "cache_control": {"type": "ephemeral"}
        }
      ]
    }
  ]
}
```

**Expected savings:** 90% on cached tokens (minimum ~1024 tokens to cache)

**Testing needed:** This is API-level; may not be controllable from Claude Code CLI or GitHub Actions. Investigate if claude-code-action supports cache control.

---

### 6.7 Explore Subagent for Context Isolation

**Source:** [Claude Code Subagents Docs](https://code.claude.com/docs/en/sub-agents)

**Claimed benefit:** Search results don't pollute main conversation context.

**How it works:**
- Explore subagent runs in isolated context
- Returns summarized findings, not raw search results
- Main conversation stays focused

**Current usage:** Already recommended in Claude Code system prompts.

**Implementation in skills:**
```markdown
### Step 2: Gather Context (Isolated)
Use the Task tool with subagent_type=Explore:
- prompt: "Find all files related to {feature}"
- model: haiku
- Return: file list with brief descriptions only
```

**Expected savings:** Prevents 1000s of tokens from search results entering main context

**Testing needed:** Compare token usage when using Explore subagent vs direct Grep/Glob in brainstorm-story skill.

---

### 6.8 Context Rot Prevention (75% Utilization Target)

**Source:** [Anthropic - Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**Claimed benefit:** Higher quality output by stopping before context degradation.

**Key insight:** "Sessions that stop at 75% utilization produce less total output but higher-quality, more maintainable code."

**The problem:**
- Context rot: performance degrades as context fills, even below technical limit
- "Effective context window" is ~256k tokens even with 1M advertised
- Running to 90% produces more bugs and architectural inconsistencies

**Implementation for workflows:**
```yaml
prompt: |
  ## Context Management Rule:
  Monitor context usage with /cost command.
  If approaching 75% context utilization:
  1. Complete current atomic task
  2. Run /compact to preserve essential context
  3. Continue or exit gracefully
```

**Expected savings:** Quality improvement, fewer bugs requiring rework

**Testing needed:** Track error rates and rework frequency in workflows that push to high context utilization vs those that stay under 75%.

---

### 6.9 /clear Between Independent Workflow Tasks

**Source:** [Builder.io - Claude Code Tips](https://www.builder.io/blog/claude-code)

**Claimed benefit:** 50-70% token reduction per session.

**Key insight:** "Reset context every 20 iterations. Performance craters after 20. Fresh start = fresh code."

**Implementation for multi-step workflows:**
```yaml
# Current pattern (single long session)
prompt: |
  1. Do task A
  2. Do task B
  3. Do task C

# Proposed pattern (fresh context per task)
jobs:
  task-a:
    prompt: "Do task A"
  task-b:
    needs: task-a
    prompt: "Do task B"
  task-c:
    needs: task-b
    prompt: "Do task C"
```

**Expected savings:** 50-70% per session, plus quality improvement

**Testing needed:** Split visualization workflow into multiple jobs, compare total tokens and output quality.

---

### 6.10 BatchPrompt Technique for Multi-Item Processing

**Source:** [Portkey - Token Efficiency](https://portkey.ai/blog/optimize-token-efficiency-in-prompts/)

**Claimed benefit:** Eliminates repeated system prompts for each item.

**How it works:**
- Process multiple items in single prompt instead of looping
- Already partially implemented via batching (section 1.4)
- Can be extended further

**Enhanced implementation:**
```markdown
### Batch Processing Format
Instead of:
- Process node 1 → output → process node 2 → output → ...

Use:
- "Process ALL of the following nodes and return a single combined output:
  1. Node A: {context}
  2. Node B: {context}
  3. Node C: {context}

  Return results in format:
  {node_id}: {result}"
```

**Expected savings:** ~500 tokens per additional item (system prompt overhead)

**Testing needed:** Enhance brainstorm-story to accept 3+ nodes in single batch, measure scaling efficiency.

---

### 6.11 Skeleton-of-Thought (SoT) Prompting

**Source:** [Portkey - Token Efficiency](https://portkey.ai/blog/optimize-token-efficiency-in-prompts/)

**Claimed benefit:** 2.39x faster generation through parallelization.

**How it works:**
1. First prompt: generate structured outline/skeleton
2. Second prompt: expand each section (can be parallelized)
3. Combine results

**Implementation for story generation:**
```markdown
### Phase 1: Generate Skeleton
"For node {ID}, generate an outline with:
- Story title
- 3 acceptance criteria headers
- Key implementation areas"

### Phase 2: Expand Skeleton
"Expand the following outline into full story format:
{skeleton}"
```

**Expected savings:** Faster generation, potentially fewer tokens through focused expansion

**Testing needed:** Implement SoT pattern in brainstorm-story, compare generation time and quality.

---

### 6.12 Memory Files for Long-Running Context

**Source:** [Claude Context Editing Docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)

**Claimed benefit:** Unbounded context through file-based memory.

**How it works:**
- Write important findings to progress/memory files
- Clear conversation context
- Load from files on-demand

**Implementation:**
```markdown
### Step N: Checkpoint to Memory
Write current findings to `ai_docs/session-memory.md`:
- Key decisions made
- Files modified
- Blockers encountered

### Step N+1: Restore from Memory (if needed)
Read `@ai_docs/session-memory.md` for context continuity
```

**Expected savings:** Enables arbitrary-length workflows without context degradation

**Testing needed:** Implement memory checkpoint in visualization workflow, test multi-session continuity.

---

## Theoretical Optimizations: Quick Reference

| Strategy | Claimed Savings | Complexity | API/CLI Level |
|----------|-----------------|------------|---------------|
| Token-efficient API beta | Variable | Low | API |
| Dynamic tool loading | 85% | High | API |
| MCP server auditing | 50-90% | Low | CLI |
| Haiku model routing | 70% cost | Medium | CLI/Skill |
| Strategic /compact | Quality | Low | CLI/Skill |
| Prompt caching | 90% cached | Medium | API |
| Explore subagent | Context isolation | Low | CLI/Skill |
| 75% utilization target | Quality | Low | CLI/Workflow |
| /clear between tasks | 50-70% | Medium | Workflow |
| BatchPrompt technique | ~500/item | Medium | Skill |
| Skeleton-of-Thought | 2.39x speed | High | Skill |
| Memory files | Unbounded | Medium | Skill/Workflow |

---

## Validation Tracking

Use this section to track which theoretical strategies have been tested:

| Strategy | Test Date | Result | Moved to Section |
|----------|-----------|--------|------------------|
| _None validated yet_ | - | - | - |

**To add a validation:**
1. Test the strategy in a real workflow
2. Document actual token savings
3. Add row to this table
4. Move strategy to appropriate validated section above
