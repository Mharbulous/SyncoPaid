# Plan: Remove "1." Prefix from Node IDs

## Overview

Remove the redundant "1." prefix from all node IDs in the story-tree database. Since there is no "2." top-level node, the leading "1." serves no purpose.

**Example transformations:**
| Current | New |
|---------|-----|
| `1.1` | `1` |
| `1.2` | `2` |
| `1.1.1` | `1.1` |
| `1.2.3` | `2.3` |
| `1.1.2.1` | `1.2.1` |
| `root` | `root` (unchanged) |

## Database Impact Analysis

### Tables & Columns to Update

| Table | Column | Records | Update Type |
|-------|--------|---------|-------------|
| `story_nodes` | `id` | 81 | Primary key - direct replacement |
| `story_paths` | `ancestor_id` | 235 | Foreign key - direct replacement |
| `story_paths` | `descendant_id` | 235 | Foreign key - direct replacement |
| `story_commits` | `story_id` | 7 | Foreign key - direct replacement |
| `vetting_decisions` | `story_a_id` | 340 | Foreign key - direct replacement |
| `vetting_decisions` | `story_b_id` | 340 | Foreign key - direct replacement |
| `vetting_decisions` | `pair_key` | 340 | Derived field - reconstruct from updated IDs |
| `story_nodes` | `notes` | ~30 | Text field - regex replacement for patterns |
| `story_nodes` | `description` | ~19 | Text field - regex replacement for patterns |

### Text Patterns to Update in Notes/Descriptions

Patterns that reference node IDs in text:
- `"story node 1.x.y"` → `"story node x.y"`
- `"story 1.x.y"` → `"story x.y"`
- `"from 1.x.y"` → `"from x.y"`
- `"with 1.x.y"` → `"with x.y"`
- `"1.x.y|1.a.b"` (pair keys in text) → `"x.y|a.b"`

## Execution Plan

### Step 1: Create Backup
- Copy `story-tree.db` to `story-tree.db.backup-YYYYMMDD`

### Step 2: Update Primary Table (story_nodes)
```sql
-- Update all node IDs (except 'root') by removing '1.' prefix
UPDATE story_nodes
SET id = SUBSTR(id, 3)
WHERE id LIKE '1.%';
```

### Step 3: Update Foreign Key Tables

#### story_paths
```sql
UPDATE story_paths
SET ancestor_id = SUBSTR(ancestor_id, 3)
WHERE ancestor_id LIKE '1.%';

UPDATE story_paths
SET descendant_id = SUBSTR(descendant_id, 3)
WHERE descendant_id LIKE '1.%';
```

#### story_commits
```sql
UPDATE story_commits
SET story_id = SUBSTR(story_id, 3)
WHERE story_id LIKE '1.%';
```

#### vetting_decisions
```sql
UPDATE vetting_decisions
SET story_a_id = SUBSTR(story_a_id, 3)
WHERE story_a_id LIKE '1.%';

UPDATE vetting_decisions
SET story_b_id = SUBSTR(story_b_id, 3)
WHERE story_b_id LIKE '1.%';

-- Regenerate pair_key from updated IDs
UPDATE vetting_decisions
SET pair_key =
  CASE
    WHEN story_a_id < story_b_id THEN story_a_id || '|' || story_b_id
    ELSE story_b_id || '|' || story_a_id
  END;
```

### Step 4: Update Text References in Notes

```sql
-- Replace patterns like "story node 1.x" or "story 1.x"
-- Use REPLACE for common patterns

-- Pattern: "node 1.X" where X is a number
UPDATE story_nodes
SET notes = REPLACE(notes, 'node 1.', 'node ')
WHERE notes LIKE '%node 1.%';

-- Pattern: "story 1.X" (without "node")
UPDATE story_nodes
SET notes = REPLACE(notes, 'story 1.', 'story ')
WHERE notes LIKE '%story 1.%' AND notes NOT LIKE '%story node%';

-- Pattern: "from 1.X"
UPDATE story_nodes
SET notes = REPLACE(notes, 'from 1.', 'from ')
WHERE notes LIKE '%from 1.%';

-- Pattern: "with 1.X"
UPDATE story_nodes
SET notes = REPLACE(notes, 'with 1.', 'with ')
WHERE notes LIKE '%with 1.%';

-- Pattern: "on 1.X"
UPDATE story_nodes
SET notes = REPLACE(notes, 'on 1.', 'on ')
WHERE notes LIKE '%on 1.%';
```

### Step 5: Update Text References in Descriptions

```sql
-- Same patterns as notes
UPDATE story_nodes
SET description = REPLACE(description, 'node 1.', 'node ')
WHERE description LIKE '%node 1.%';

UPDATE story_nodes
SET description = REPLACE(description, 'story 1.', 'story ')
WHERE description LIKE '%story 1.%' AND description NOT LIKE '%story node%';
```

### Step 6: Verify Integrity

```sql
-- Check no orphaned references
SELECT * FROM story_paths
WHERE ancestor_id NOT IN (SELECT id FROM story_nodes)
   OR descendant_id NOT IN (SELECT id FROM story_nodes);

SELECT * FROM story_commits
WHERE story_id NOT IN (SELECT id FROM story_nodes);

SELECT * FROM vetting_decisions
WHERE story_a_id NOT IN (SELECT id FROM story_nodes)
   OR story_b_id NOT IN (SELECT id FROM story_nodes);

-- Verify node count unchanged
SELECT COUNT(*) FROM story_nodes;  -- Should be 81

-- Sample verification
SELECT id FROM story_nodes ORDER BY id LIMIT 20;
```

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Data loss | Backup created before changes |
| Foreign key violations | Disable FK checks during update, re-enable after |
| Missed text references | Manual review of notes/descriptions after update |
| External references | Check for node IDs in `.claude/data/plans/` markdown files |

## Additional Files to Update

### Plan Files with Node IDs in Filenames (13 files to rename)

| Current Filename | New Filename |
|------------------|--------------|
| `1-2-6-screenshot-retention-cleanup.md` | `2-6-screenshot-retention-cleanup.md` |
| `1.2.10-screenshot-categorization-ui.md` | `2.10-screenshot-categorization-ui.md` |
| `1.8-llm-ai-integration.md` | `8-llm-ai-integration.md` |
| `1.8.2-browser-url-extraction.md` | `8.2-browser-url-extraction.md` |
| `2025-12-16-1.8.3-ui-automation-integration.md` | `2025-12-16-8.3-ui-automation-integration.md` |
| `2025-12-17-1-8-1-matter-client-database.md` | `2025-12-17-8-1-matter-client-database.md` |
| `2025-12-17-1-8-4-2-transition-detection-smart-prompts.md` | `2025-12-17-8-4-2-transition-detection-smart-prompts.md` |
| `2025-12-17-1.2.9-monthly-screenshot-archiving.md` | `2025-12-17-2.9-monthly-screenshot-archiving.md` |
| `2025-12-17-1.8.4-ai-disambiguation-foundation.md` | `2025-12-17-8.4-ai-disambiguation-foundation.md` |
| `2025-12-18-1.1.2.1-idle-resumption-detection.md` | `2025-12-18-1.2.1-idle-resumption-detection.md` |
| `2025-12-18-1.1.2.2-lock-screen-and-screensaver-detection.md` | `2025-12-18-1.2.2-lock-screen-and-screensaver-detection.md` |
| `2025-12-18-1.1.6-enhanced-context-extraction.md` | `2025-12-18-1.6-enhanced-context-extraction.md` |

### Plan File Contents

Update node ID references inside the 14 plan files:
- Replace `1.x.y` patterns with `x.y` in file contents
- Ensure cross-references remain valid

## Rollback Plan

If issues are discovered:
```bash
cp .claude/data/story-tree.db.backup-YYYYMMDD .claude/data/story-tree.db
```

## Approval Requested

Please review this plan and confirm:
1. The transformation logic is correct (`1.x.y` → `x.y`)
2. All identified tables and columns are correct
3. The text replacement patterns cover expected cases
4. Ready to proceed with execution
