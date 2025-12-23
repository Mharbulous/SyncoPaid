# Handover: Add Semantic Analysis Phase to story-arborist Skill

## Objective

The story-arborist skill is incomplete. It was designed to have two phases:
1. **Structural health** (deterministic scripts) — implemented
2. **Semantic organization** (AI analysis) — **MISSING**

Add Phase 2 guidance to SKILL.md so Claude can analyze semantic organization after structural issues are resolved.

## Key Files

**Skill to update:**
- `.claude/skills/story-arborist/SKILL.md`

**Database for testing:**
- `.claude/data/story-tree.db` (NOT the empty `story-tree.db` in repo root)

**Schema reference:**
- `.claude/skills/story-tree/utility/story_db_common.py`

## Current State

SKILL.md covers structural issues only:
- Orphaned nodes
- Invalid root children (decimal IDs at depth-1)
- Missing self-paths
- Parent mismatch
- Invalid ID format

`tree_health.py` reports "HEALTHY" even when semantic issues exist.

## Semantic Issues to Detect

These were identified during a manual review that the skill should have surfaced:

| Indicator | Detection Method | Red Flag Example |
|-----------|------------------|------------------|
| **Leaf epics** | Depth-1 nodes with 0 children | Nodes 16-20 (implementation details at epic level) |
| **Feature fragmentation** | Related keywords spread across multiple parents | 7 AI-related nodes at depth-1 that should be 2 |
| **Granularity mismatch** | Title specificity inappropriate for depth | "Moondream 2 Integration (CPU-Friendly)" at depth-1 |
| **Overlapping features** | Similar titles/descriptions under different parents | [15] duplicates [8]'s purpose |
| **Rejected clutter** | Rejected/archived nodes still at depth-1 | [10], [11] rejected but still prominent |

## What to Add to SKILL.md

### 1. Phase 2 Section

After "Step 4: Verify" add a new workflow phase:

```markdown
## Phase 2: Semantic Organization Review

After structural issues are resolved, analyze semantic organization.

### Semantic Health Indicators

| Indicator | How to Check | Action |
|-----------|--------------|--------|
| Leaf epics | Query depth-1 nodes with 0 children | Consider demoting to depth-2 |
| Feature fragmentation | Group nodes by keyword, check parent distribution | Consolidate under single epic |
| Granularity mismatch | Compare title specificity to depth | Move to appropriate depth |
| Overlapping features | Compare descriptions of sibling epics | Merge or clarify boundaries |
| Rejected clutter | Check disposition of depth-1 nodes | Archive or delete |
```

### 2. Diagnostic Queries

Add SQL queries Claude can run to surface semantic issues:

```sql
-- Leaf epics (depth-1 with no children)
SELECT n.id, n.title, n.stage, n.disposition
FROM story_nodes n
JOIN story_paths p ON p.descendant_id = n.id AND p.ancestor_id = 'root' AND p.depth = 1
WHERE NOT EXISTS (
    SELECT 1 FROM story_paths p2 WHERE p2.ancestor_id = n.id AND p2.depth = 1
);

-- Depth-1 distribution
SELECT n.id, n.title,
    (SELECT COUNT(*) FROM story_paths p WHERE p.ancestor_id = n.id AND p.depth > 0) as descendants
FROM story_nodes n
JOIN story_paths p ON p.descendant_id = n.id AND p.ancestor_id = 'root' AND p.depth = 1
ORDER BY descendants;
```

### 3. Guidelines for Epic vs Feature vs Task

Add heuristics:
- **Epic (depth-1)**: Broad capability area, should have 3+ children, title is a noun phrase
- **Feature (depth-2)**: Specific functionality, may have sub-tasks, title describes what it does
- **Task (depth-3+)**: Implementation detail, typically a leaf node, title is actionable

## Example Semantic Issue

Current tree has 7 AI-related depth-1 nodes:
```
[8]  LLM & AI Integration (9 descendants)     ← Keep, rename
[15] AI Screenshot Intelligence (10 desc)     ← Merge into [8]
[16] Local LLM Engine Architecture (0 desc)   ← Demote
[17] Hardware Detection & Model Selection (0) ← Demote
[18] Moondream 2 Integration (0)              ← Demote
[19] Moondream 3 Integration (0)              ← Demote
[20] First-Run Model Download (0)             ← Demote
```

Proposed consolidation: 2 depth-1 nodes
- `[8] AI-Powered Time Categorization` — user-facing AI features
- `[NEW] Local AI Engine` — infrastructure (absorbs 16-20)

## Acceptance Criteria

1. SKILL.md has Phase 2 section with semantic analysis workflow
2. Diagnostic queries are documented for Claude to run
3. Guidelines distinguish epic vs feature vs task
4. Skill description updated to mention both structural and semantic analysis
