# Analyze Story Database for Existing Conflicts

## Task

Examine the current story-tree database to assess whether conflicting or duplicate stories already exist. Determine if Claude's judgment during story generation has been sufficient, or if programmatic conflict detection is needed.

## Context

The story-tree orchestrator generates stories autonomously via GitHub Actions. Current duplicate prevention relies solely on:
1. Providing existing children context to Claude
2. Prompt instructions: "avoid duplicates by reviewing existing children"

**No programmatic similarity checking exists.** We designed a schema extension (`ai_docs\Orchestrator\2025-12-16-Problem-Space-Schema.md`) but want to validate the problem exists before implementing.

## Database Location

`.claude\data\story-tree.db` (SQLite)

## Analysis Steps

1. **Export all stories** with their descriptions
2. **Group by parent** - siblings are most likely to conflict
3. **Identify candidates** for:
   - **Duplicates**: Same feature, different wording
   - **Scope overlap**: One story subsumes another
   - **Architectural conflict**: Incompatible technical approaches (e.g., local SQLite vs cloud Firestore)
   - **Competing solutions**: Same problem, different approaches

4. **Report findings** with specific story IDs and descriptions

## Key Files

| File | Purpose |
|------|---------|
| `.claude\data\story-tree.db` | Story database |
| `.claude\skills\story-tree\references\schema.sql` | Current schema (v3) |
| `ai_docs\Orchestrator\2025-12-16-Problem-Space-Schema.md` | Proposed conflict detection schema |
| `ai_docs\Orchestrator\2025-12-16-Dev-Workflow.md` | Orchestrator documentation |

## Useful Queries

```sql
-- All stories with parent
SELECT s.id, s.title, s.description, s.status,
       (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
FROM story_nodes s
WHERE s.id != 'root'
ORDER BY parent_id, s.id;

-- Stories grouped by parent (find siblings)
SELECT parent.id as parent_id, parent.title as parent_title,
       GROUP_CONCAT(child.id, ', ') as children
FROM story_nodes parent
JOIN story_paths sp ON sp.ancestor_id = parent.id AND sp.depth = 1
JOIN story_nodes child ON child.id = sp.descendant_id
GROUP BY parent.id
HAVING COUNT(*) > 1;

-- Story count by status
SELECT status, COUNT(*) FROM story_nodes GROUP BY status ORDER BY COUNT(*) DESC;
```

## Conflict Types to Look For

| Type | Example Pattern |
|------|-----------------|
| **Duplicate** | "Export to PDF" and "PDF export functionality" |
| **Scope overlap** | "File-level balance" vs "Client-wide balance dashboard" |
| **Architectural** | Story assumes SQLite; another assumes Firestore |
| **Sequencing** | Story A needs B done first; Story B needs A done first |

## Research Context (from web search)

- **S3CDA algorithm**: Two-phase conflict detection using sentence embeddings + cosine similarity ([arXiv](https://arxiv.org/html/2206.13690))
- **ADRs**: Architecture Decision Records track why choices were made ([adr.github.io](https://adr.github.io/))
- **IBIS**: Issue-Based Information Systems capture alternatives considered ([Wikipedia](https://en.wikipedia.org/wiki/Issue-based_information_system))

## NOT Relevant

- `.claude\data\insert_stories.py` - Contains screenshot deduplication code, not story deduplication
- `ai_docs\Handovers\Completed\*` - Historical, already done

## Deliverables

1. Summary of database size and composition
2. List of potential conflicts found (with story IDs and why they conflict)
3. Assessment: Is programmatic conflict detection needed at current scale?
4. Recommendation: Implement schema extension now, later, or not at all
