# Write-Story GitHub Action: Token Efficiency Analysis

**Date:** 2025-12-16
**Workflow Run:** https://github.com/Mharbulous/SyncoPaid/actions/runs/20261831703
**Duration:** 4 minutes 7 seconds
**Status:** Success

## Executive Summary

The `/write-stories` workflow successfully generated concept stories but exhibits several token inefficiencies in its multi-layer architecture. The primary issues are:

1. **Verbose skill documents** loaded on every invocation (~1,100+ lines total)
2. **Redundant context loading** (CLAUDE.md, vision files, git history)
3. **Multi-layer delegation** with repeated context at each layer
4. **Unnecessary full git checkout** when only 30 days of commits are analyzed

**Estimated potential savings:** 40-60% token reduction possible with targeted optimizations.

---

## Current Architecture Analysis

### Execution Chain

```
GitHub Action Workflow
    │
    ├── 1. Prompt (~100 lines)
    │       └── "Read CLAUDE.md, run /write-stories"
    │
    └── 2. /write-stories command (write-story.md: 236 lines)
            │
            ├── SQL: Find under-capacity nodes
            ├── SQL: Find stories needing refinement
            │
            └── 3. story-writing skill (SKILL.md: 563 lines)
                    │
                    ├── Check vision files
                    ├── Query parent node context
                    ├── Analyze git commits
                    ├── Generate stories
                    └── Output detailed report
```

### Token Consumption Breakdown (Estimated)

| Component | Size | Loaded When | Token Impact |
|-----------|------|-------------|--------------|
| Workflow prompt | ~100 lines | Every run | ~500 tokens |
| CLAUDE.md | ~80 lines | Instructed to read | ~400 tokens |
| write-story.md | 236 lines | Command expansion | ~1,200 tokens |
| story-writing SKILL.md | 563 lines | Skill invocation | ~2,800 tokens |
| story-tree SKILL.md | 334 lines | If referenced | ~1,700 tokens |
| Vision files (if exist) | ~50-100 lines | Per check | ~500 tokens |
| **Total overhead per run** | | | **~7,000+ tokens** |

---

## Identified Inefficiencies

### 1. Redundant CLAUDE.md Reading

**Location:** `.github/workflows/write-stories.yml` line 61

```yaml
prompt: |
  1. Read CLAUDE.md for project conventions
```

**Issue:** CLAUDE.md content is already available in context via `claudeMd` system reminders. Explicitly reading it again adds ~400 tokens.

**Recommendation:** Remove this instruction. Claude already has access to CLAUDE.md content.

**Savings:** ~400 tokens

---

### 2. Verbose Skill Documents

**Location:** `.claude/skills/story-writing/SKILL.md` (563 lines)

**Issue:** The skill document contains:
- 15+ code block examples (~200 lines)
- 3 complete story examples (~80 lines)
- "Common Mistakes" table repeated patterns (~50 lines)
- "Quality Checks Checklist" duplicated sections (~40 lines)

**Analysis:** Every skill invocation processes the entire 563-line document even though:
- Examples are rarely needed for an automated CI workflow
- Quality checklists are verbose and repetitive
- Common mistakes tables repeat across multiple skills

**Recommendation:** Create a "CI-optimized" variant of the skill or split into:
- Core workflow instructions (required)
- Reference examples (load on demand)
- Quality checklists (abbreviated version for CI)

**Potential savings:** ~1,400 tokens (50% of skill document)

---

### 3. Multi-Step Vision File Checking

**Location:** story-writing SKILL.md, Step 0

```python
# Step 0.1: Check existence
python -c "import os; print(os.path.exists('ai_docs/non-goals.md'))"

# Step 0.2: If exists, read file
# (separate operation)
```

**Issue:** Two separate Python executions plus parsing. The existence check outputs to Claude, then a separate read operation occurs.

**Recommendation:** Combine into single operation that checks + reads in one step:
```python
python -c "
import os, json
result = {'vision': None, 'anti_vision': None}
for name, path in [('vision', 'ai_docs/non-goals.md'), ('anti_vision', 'ai_docs/user-non-goals.md')]:
    if os.path.exists(path):
        with open(path) as f: result[name] = f.read()
print(json.dumps(result))
"
```

**Savings:** ~200 tokens (reduced back-and-forth)

---

### 4. Full Git History Checkout

**Location:** `.github/workflows/write-stories.yml` line 27

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0  # Full history for git operations
```

**Issue:** Downloads full git history but the skill only analyzes `--since=30 days ago`:

```python
# In story-writing SKILL.md
cmd = ['git', 'log', '--since=30 days ago', ...]
```

**Impact:** Checkout time and network overhead (not token-related, but affects overall workflow duration).

**Recommendation:** Use `fetch-depth: 100` or a shallow clone with date-based filter:
```yaml
fetch-depth: 0
fetch-tags: false
```

Or calculate appropriate depth based on commit frequency.

**Savings:** Reduces checkout time, minimal token impact but improves CI efficiency.

---

### 5. Two-Phase Node Discovery

**Location:** `.claude/commands/write-story.md` lines 18-80

**Issue:** The command runs two separate SQL queries:
1. Find under-capacity nodes (lines 18-50)
2. Find stories needing refinement (lines 53-80)

Then for each result, it invokes the story-writing skill separately.

**Recommendation:** Combine into a single query with UNION or restructure:
```python
python -c "
import sqlite3, json
conn = sqlite3.connect('.claude/data/story-tree.db')
# Single query: nodes needing attention (under-capacity OR refine status)
cursor.execute('''
    SELECT id, title, 'capacity' as reason FROM ...
    UNION
    SELECT id, title, 'refine' as reason FROM ... WHERE status = 'refine'
''')
print(json.dumps([dict(r) for r in cursor.fetchall()]))
"
```

**Savings:** ~300 tokens (reduced SQL duplication and output parsing)

---

### 6. Inline SQL Query Verbosity

**Location:** Multiple skills (write-story.md, story-writing SKILL.md)

**Issue:** Full SQL queries are written inline with extensive formatting:
```sql
SELECT s.id, s.title, s.status,
    (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
    COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
         JOIN story_nodes child ON sp.descendant_id = child.id
         WHERE sp.ancestor_id = s.id AND sp.depth = 1
         AND child.status IN ('implemented', 'ready'))) as effective_capacity
...
```

**Recommendation:** Extract SQL queries to a shared file (e.g., `.claude/skills/story-tree/references/sql-queries.md`) and reference them, OR create Python utility scripts that encapsulate common queries.

**Savings:** ~400 tokens (consolidated query definitions)

---

### 7. Report Generation Verbosity

**Location:** story-writing SKILL.md, Step 7

**Issue:** The skill generates a verbose markdown report including:
- Full story text (already inserted to database)
- Vision alignment summaries
- Gap analysis details
- Git commits list

For CI automation, this detailed output is captured in logs but adds significant tokens to the conversation.

**Recommendation:** Add a `--quiet` or `--ci` mode that outputs minimal confirmation:
```
Generated 2 stories for node 1.2: [1.2.4] Configure polling, [1.2.5] Add export filter
```

**Savings:** ~500 tokens (reduced report generation)

---

### 8. Skill Layer Delegation Overhead

**Current pattern:**
```
write-story.md → story-writing skill
                 └── (each invocation loads full skill doc)
```

**Issue:** If generating stories for 2 nodes, the story-writing skill document (563 lines) is conceptually "loaded" twice in Claude's reasoning.

**Recommendation:** Consider batching - instead of invoking the skill per-node, pass all target nodes in one invocation:
```
story-writing --nodes "1.2,1.3" --max-stories-per-node 1
```

**Savings:** ~1,400 tokens (avoid duplicate skill doc processing)

---

## Optimization Priority Matrix

| Optimization | Effort | Token Savings | Recommendation |
|-------------|--------|---------------|----------------|
| Remove CLAUDE.md read instruction | Low | ~400 | **Do immediately** |
| Create CI-mode skill variant | Medium | ~1,400 | High priority |
| Batch node processing | Medium | ~1,400 | High priority |
| Combine vision file checks | Low | ~200 | Easy win |
| Consolidate SQL queries | Medium | ~400 | Medium priority |
| Simplify report output | Low | ~500 | Easy win |
| Optimize git checkout | Low | ~0 (time only) | Nice to have |
| Single node discovery query | Low | ~300 | Easy win |

**Total potential savings:** ~4,600 tokens (~40-65% reduction)

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (Immediate)

1. **Remove explicit CLAUDE.md read** from workflow prompt
2. **Add `--ci` flag** to story-writing that:
   - Skips verbose examples section processing
   - Outputs minimal confirmation instead of full report
3. **Combine vision file checks** into single Python execution

### Phase 2: Structural Improvements

1. **Create batched story generation** - modify write-story.md to collect all target nodes, then invoke story-writing once with all nodes
2. **Extract SQL queries** to shared utility or reference file
3. **Consolidate node discovery** into single query

### Phase 3: Advanced Optimizations

1. **Create skill variants** - `SKILL.md` (full) vs `SKILL-CI.md` (minimal)
2. **Precompute context** - Store frequently-used query results in metadata table
3. **Consider dedicated CI agent** - A streamlined subagent optimized for scheduled tasks

---

## Baseline Metrics (For Future Comparison)

| Metric | Value | Notes |
|--------|-------|-------|
| Workflow duration | 4m 7s | First successful run |
| Stories generated | 2 | Per workflow constraints |
| Estimated tokens | ~7,000+ | Based on document analysis |
| Commit hash | c751d3b | "stories: auto-generate concept stories" |

---

## Files Involved in Optimization

| File | Lines | Purpose | Action |
|------|-------|---------|--------|
| `.github/workflows/write-stories.yml` | 101 | Workflow definition | Modify prompt |
| `.claude/commands/write-story.md` | 236 | Command orchestration | Batch processing |
| `.claude/skills/story-writing/SKILL.md` | 563 | Story generation | Create CI variant |
| `.claude/skills/story-tree/SKILL.md` | 334 | Tree management | Reference only |

---

## Next Steps

1. Create issue or task for implementing Phase 1 optimizations
2. Run A/B comparison after Phase 1 to measure actual token reduction
3. Document token usage metrics if Claude Code exposes them
4. Consider adding telemetry to track optimization effectiveness

---

## References

- Workflow run: https://github.com/Mharbulous/SyncoPaid/actions/runs/20261831703
- Write-story command: `.claude/commands/write-story.md`
- story-writing skill: `.claude/skills/story-writing/SKILL.md`
- Previous analysis: `ai_docs/Research/2025-12-16-slash-commands-vs-skills-analysis.md`
