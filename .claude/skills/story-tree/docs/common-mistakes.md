# Common Mistakes

This document catalogs common pitfalls when using the story-tree skill and how to avoid them. These mistakes were identified through RED-GREEN-REFACTOR testing with subagents.

---

## Mistake 1: Generating Vague Stories

### Problem

Creating stories with generic descriptions that aren't specific or testable:

```markdown
### 1.2.3: Improve UX
**As a** user
**I want** better experience
**So that** I'm happier
```

### Why It's Wrong

- Not specific (what aspect of UX?)
- Not testable (what does "better" mean?)
- No clear value (why does this matter?)
- No connection to git evidence

### How to Fix

Use git analysis to be specific:

```markdown
### 1.2.3: Add keyboard shortcuts to document table
**As a** lawyer reviewing hundreds of documents
**I want** keyboard shortcuts for common actions (next/prev, tag, flag)
**So that** I can review documents 40% faster without reaching for the mouse

**Acceptance Criteria**:
- [ ] Arrow keys navigate to next/previous document
- [ ] 'T' key opens tagging menu
- [ ] 'F' key toggles flag status
- [ ] Shortcuts shown in help menu (?)
- [ ] Shortcuts work with virtual scrolling table

**Suggested capacity**: 3
**Rationale**: Git commits show keyboard handling in UploadTable.vue (29 changes). Similar navigation feature has capacity 3.
**Related context**: Commits a1b2c3d reference keyboard events
```

### Prevention

- Always reference git commits, file changes, or existing patterns
- Include specific user roles ("lawyer" not "user")
- Use measurable benefits ("40% faster" not "happier")
- Write testable acceptance criteria

---

## Mistake 2: Ignoring the Priority Algorithm

### Problem

Choosing nodes based on intuition rather than the documented algorithm:

> "Node 1.3.2.1 is completely empty (0/3), so that's the highest priority."

### Why It's Wrong

The priority algorithm explicitly states:
- **Primary sort**: Depth (shallower = higher priority)
- **Secondary sort**: Fill rate (emptier = higher priority)

Depth takes absolute precedence over fill rate.

### Correct Algorithm Application

Given these under-capacity nodes:
- Root (5/10, depth 0, 50% fill) ← **THIS IS PRIORITY**
- Node 1.2 (0/5, depth 1, 0% fill) ← Not priority (deeper)
- Node 1.3.2.1 (0/3, depth 3, 0% fill) ← Not priority (even deeper)

The shallowest node (Root at depth 0) wins, even though it has a higher fill rate than the others.

### Why It Matters

**Breadth-first growth** creates balanced product portfolio before diving deep:
- Ensures strategic options at high levels
- Prevents over-commitment to single path
- Maintains flexibility for pivots
- Follows best practices in product planning

### Prevention

Always follow the algorithm explicitly:
1. Filter to under-capacity nodes
2. Sort by depth (ascending)
3. Break ties by fill rate (ascending)
4. Select first node

---

## Mistake 3: Not Matching Commits to Existing Stories

### Problem

Generating new stories without checking if recent commits should update existing story statuses.

### Why It's Wrong

- Stories stay "in-progress" even though they're implemented
- Tree metrics are inaccurate
- Duplicate work (generating stories that already exist)
- Missing implementation evidence

### How to Fix

Always run Step 2 (git analysis) before Step 5 (story generation):

```bash
# Step 2: Analyze commits
git log --since="30 days ago" --pretty=format:"%h|%s" --no-merges

# Match to existing stories
# If story 1.1.3 "Document table view" matches 5 commits with "table" keywords:
# - Update status from "in-progress" to "implemented"
# - Add commit hashes to implementedCommits array: ["a1b2c3d", "d4e5f6g", ...]
# - Update lastImplemented timestamp
```

### Pattern Matching Example

Story: "Upload evidence files" → keywords: ["upload", "evidence", "file", "files"]
Commit: "feat: Add drag-and-drop file upload" → keywords: ["add", "drag", "drop", "file", "upload"]

Matching keywords: ["file", "upload"] = 2
Jaccard similarity = 2 / (4 + 5 - 2) = 2/7 = 0.29 (below 0.7 threshold)

This commit doesn't match - need >70% similarity.

### Prevention

- Run commit analysis before story generation (always)
- Use the pattern matcher algorithm from `lib/pattern-matcher.md`
- Update status when commits match with >70% confidence
- Document commit hashes in `implementedCommits` array

---

## Mistake 4: Capacity Estimates Too High or Too Low

### Problem

Using the same capacity for every story regardless of complexity:

```markdown
### 1.1.1: Login button (capacity: 5)
### 1.1.2: Email threading system (capacity: 5)
### 1.1.3: Entire EDRM workflow (capacity: 5)
```

### Why It's Wrong

Capacity should reflect expected breakdown granularity:
- Login button needs 2-3 children (states, error handling, loading)
- Email threading needs 8-10 children (parsing, tree building, UI, search)
- EDRM workflow needs 10-15 children (8 phases + reporting + audit)

Using uniform capacity leads to:
- Shallow trees (under-detailed features)
- Mismatched expectations
- Poor planning

### How to Fix

Use context-based estimation:

| Story Type | Typical Capacity | Reasoning |
|------------|-----------------|-----------|
| **Simple UI component** | 2-3 | Single component, few props, minimal logic |
| **Feature with workflow** | 5-8 | Multiple components, state management, API calls |
| **Major feature** | 8-12 | End-to-end system, multiple integrations, complex UX |
| **Cross-cutting concern** | 10-15 | Affects many areas, requires coordination |

### Examples from Testing

- "Drag-and-drop upload" = 2 (single interaction pattern)
- "Email threading" = 8 (parsing, tree building, visualization, search integration)
- "EDRM workflow" = 12 (8 phases, compliance requirements, audit trails)

### Prevention

- Look at similar implemented stories to calibrate
- Consider: user roles, business logic complexity, integrations, UI/UX scope
- Use `lib/capacity-management.md` guidelines
- Adjust capacity based on git evidence (file change patterns)

---

## Mistake 5: Not Using Quality Checks Checklist

### Problem

Generating stories without validating them against the quality checks (main SKILL.md lines 377-385).

### Why It's Wrong

Low-quality stories create confusion and rework:
- Vague stories → team doesn't know what to build
- Untestable criteria → can't verify completion
- Duplicate stories → wasted effort
- Misaligned stories → doesn't fit architecture

### How to Fix

Before outputting generated stories, verify EVERY item:

- [ ] **Clear basis**: Each story has evidence in commit history or gap analysis
- [ ] **Specific**: Stories are actionable, not "improve UX"
- [ ] **Testable criteria**: Acceptance criteria can verify when complete
- [ ] **No duplicates**: Check existing stories before adding
- [ ] **Aligned**: Stories fit existing architecture patterns
- [ ] **Reasonable capacity**: Estimates match similar past work
- [ ] **Complete format**: Includes "As a.../I want.../So that..."

### Example Quality Check

**Story to validate**:
```markdown
### 1.2.5: Add search
**As a** user
**I want** search
**So that** I find things
```

**Checklist results**:
- [❌] Clear basis - No git evidence or gap analysis mentioned
- [❌] Specific - "search" is too vague (search what? how?)
- [❌] Testable criteria - No acceptance criteria at all
- [?] No duplicates - Need to check existing stories
- [❌] Aligned - No architecture context
- [❌] Reasonable capacity - No capacity estimate
- [❌] Complete format - Missing specific user role and benefit

**Verdict**: REJECT this story, generate a better one.

### Prevention

- Make quality checks the FINAL step before output
- If ANY checklist item fails, revise the story
- Don't output stories "good enough" - they must be excellent
- Use the checklist as acceptance criteria for your own output

---

## Mistake 6: Working with Hypothetical vs Real Data

### Problem

User describes a hypothetical project ("TaskFlow app") but you're in a real codebase ("Listbot").

Should you:
- A) Work with the hypothetical scenario?
- B) Work with the real codebase?

### Why It's Confusing

The story-tree skill is designed to analyze **actual git history** and **actual code patterns**. Hypothetical scenarios have no git evidence.

### How to Fix

**Always work with the real codebase you have access to.**

When user mentions a hypothetical scenario:

1. **Acknowledge the mismatch**:
   ```
   "I notice you mentioned a 'TaskFlow' project, but I'm currently in the Listbot repository."
   ```

2. **Explain the constraint**:
   ```
   "The story-tree skill analyzes real git commits and codebase patterns, so I'll generate stories based on the **actual Listbot development activity**."
   ```

3. **Proceed with real data**:
   ```
   "Analyzing the last 30 days of commits in the Listbot repository..."
   ```

### Why Real Data Only

Git-based pattern detection requires:
- Actual commit messages to extract keywords
- File change frequency to identify focus areas
- Implementation evidence to update story status
- Architecture patterns to guide capacity estimates

None of this exists for hypothetical projects.

### When Hypotheticals Are Appropriate

If the user wants to explore hypothetical scenarios:
- Discuss them conversationally
- Don't use the story-tree skill
- Don't create hypothetical story-tree.json files
- Keep it separate from the real backlog

### Prevention

- Always check: "Am I in a real codebase with git history?"
- If yes: Proceed autonomously with real data
- If no: Inform user that skill requires real git history
- Don't mix hypothetical stories with real backlog

---

## Mistake 7: Copy-Pasting SQL Queries Without Validation

### Problem

Copying SQL queries from documentation without testing them against the actual database:

```sql
-- Copied from docs, but uses wrong table name
SELECT * FROM stories WHERE status = 'implemented';
-- Error: no such table: stories
```

### Why It's Wrong

- Documentation can drift from actual schema
- Table/column names may have been renamed during refactoring
- Untested queries fail at runtime, disrupting workflow

### How to Fix

**Always validate queries before using them:**

```bash
# Quick validation - run query and check for errors
sqlite3 .claude/data/story-tree.db "SELECT * FROM story_nodes LIMIT 1;"

# Validate all queries in a file (extract and test)
grep -oP "(?<=\`\`\`sql)[\s\S]*?(?=\`\`\`)" docs/file.md | \
    while read query; do sqlite3 .claude/data/story-tree.db "$query"; done
```

**Correct table/column names (as of v2.0.0):**
- Table: `story_nodes` (not `stories`)
- Table: `story_paths` (not `story_tree` or `story_hierarchy`)
- Table: `story_commits` (not `story_node_commits`)
- Column: `title` (not `story` or `name`)

### Prevention

- Test queries against actual database before documenting
- When refactoring schema, search docs for old names
- Use schema.sql as source of truth for table/column names

---

## Quick Reference: Mistake Checklist

Before outputting generated stories, verify you didn't make these mistakes:

- [ ] **Not Mistake 1**: Stories are specific with testable criteria (not vague)
- [ ] **Not Mistake 2**: Used priority algorithm (shallower nodes first)
- [ ] **Not Mistake 3**: Matched commits to existing stories before generating new ones
- [ ] **Not Mistake 4**: Capacity estimates vary by complexity (not uniform)
- [ ] **Not Mistake 5**: All quality checks passed
- [ ] **Not Mistake 6**: Used real git data (not hypothetical scenarios)
- [ ] **Not Mistake 7**: SQL queries validated against actual schema

If any checkbox fails, fix the issue before proceeding.

---

## Version History

- v1.1.0 (2025-12-11): Added Mistake 7 (SQL query validation)
- v1.0.0 (2025-12-11): Initial documentation from RED-GREEN-REFACTOR testing
