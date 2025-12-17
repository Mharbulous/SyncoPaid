# Handover: Story Vetting Conflict Classification Cache

## Objective
Add persistent caching to story-vetting skill to avoid repeatedly running expensive LLM classifications on the same story pairs daily.

## Problem Statement
The story-vetting skill runs in two phases:
1. **Phase 1 (cheap)**: Heuristics flag potential conflicts using keyword/similarity matching
2. **Phase 2 (expensive)**: LLM classifies each candidate as duplicate/overlap/competing/incompatible/false_positive

Current issue: With 77 stories, Phase 1 generates **238 candidate pairs**. When run daily, the same pairs get re-analyzed repeatedly, wasting tokens.

## Current Implementation

### Key Files
- `.claude/skills/story-vetting/SKILL.md` - Complete skill documentation with decision matrix
- `.claude/skills/story-vetting/vetting_processor.py` - Phase 2 processor (incomplete)
- `.claude/data/story-tree.db` - SQLite database with story_nodes and story_paths tables
- `.claude/skills/story-tree/references/schema.sql` - Database schema reference

### Phase 1 Heuristics (Python in SKILL.md)
Flags pair as candidate if any signal exceeds threshold:
- Shared specific keywords ≥1 (e.g., "sqlite", "archiving", "ui_automation")
- Title Jaccard similarity >0.15
- Title overlap coefficient >0.4
- Description Jaccard similarity >0.10

### Phase 2 Classification Types
- `duplicate` - Same story → auto-merge or delete
- `scope_overlap` - Partial overlap → merge or human review
- `competing` - Same problem, different approaches → merge/reject/block based on status
- `incompatible` - Mutually exclusive → pick better, delete other
- `false_positive` - Not actually conflicting → skip

### Decision Matrix
See SKILL.md for full matrix. Key pattern:
- concept vs implemented/planned/approved with weak signals → usually false_positive
- concept vs concept → usually needs classification
- Automated actions determined by conflict type + statuses

## What Was Tried
Implemented Phase 1 detection successfully (238 candidates from 77 stories). Started Phase 2 but **user aborted** when recognizing the repeated LLM cost problem.

Quick classification heuristic attempted but only filters ~150-180 false positives, leaving ~50-90 needing LLM review **every day**.

## Solution Design Task

Design persistent cache to store previous conflict classifications. Requirements:

1. **Store**: Story pair ID + classification + timestamp of decision
2. **Query**: During Phase 1, skip pairs already classified as false_positive
3. **Invalidate**: If either story in pair changes (description/status), re-analyze
4. **Integrate**: Phase 1 checks cache before adding to candidates list

### Data Structure Considerations
- Array of booleans (true=conflict, false=false_positive)?
- Hash table with pair IDs as keys?
- New SQLite table in story-tree.db?
- Separate cache database?
- What pair ID format? "1.1|1.8.4.1" with canonical ordering?

### Schema Questions
- Track just false_positives, or all classifications?
- Store confidence scores for later review?
- Track which heuristic triggered the pairing?
- How to detect story changes for cache invalidation?

## Technical Context

### Story Database Schema
```sql
story_nodes (id TEXT PRIMARY KEY, title TEXT, description TEXT, status TEXT, notes TEXT)
story_paths (ancestor_id TEXT, descendant_id TEXT, depth INTEGER)
```

### Python Environment
- Python 3.11+
- SQLite3 module (NOT CLI)
- Working directory: C:\Users\Brahm\Git\SyncoPaid
- Database: .claude/data/story-tree.db

## Next Steps
1. Research conflict caching patterns (web search: "conflict detection caching patterns", "pairwise comparison cache invalidation")
2. Design cache schema considering query performance and invalidation
3. Implement cache table and integrate into Phase 1 filtering
4. Test that repeated runs skip previously classified pairs

## References
- Story-vetting skill: `.claude/skills/story-vetting/SKILL.md`
- Story-tree schema: `.claude/skills/story-tree/references/schema.sql`
- SQL query patterns: `.claude/skills/story-tree/references/sql-queries.md`
