Generate new user story concepts using the story-writing skill, or refine existing stories that need rework.

## Arguments

- **With arguments**: Pass the arguments as instructions to the story-writing skill (e.g., `/write-story for node 1.2` or `/write-story focus on export features`)
- **Without arguments**: Auto-discover nodes with capacity for new stories AND nodes with status 'refine' that need rework

## Default Behavior (No Arguments)

When invoked without arguments, the command performs two distinct operations:
1. **Generate new stories** for nodes with capacity
2. **Refine existing stories** that have status 'refine'

### Step 1: Discover All Nodes Needing Attention

Query the story-tree database in a single call to find:
- Up to 1 node with capacity for new stories
- Up to 2 stories needing refinement (status 'refine')

**Note:** These limits are optimized for token efficiency. Refinements are more intensive (~2,000-2,500 tokens each) so we limit the batch size. The skill will be called again if more work remains.

```python
python -c "
import sqlite3
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

result = {'capacity_nodes': [], 'refine_nodes': []}

# Find under-capacity nodes, shallower first (limit 2)
cursor.execute('''
    SELECT s.id, s.title, s.status,
        (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) as child_count,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
        COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
             JOIN story_nodes child ON sp.descendant_id = child.id
             WHERE sp.ancestor_id = s.id AND sp.depth = 1
             AND child.status IN ('implemented', 'ready'))) as effective_capacity
    FROM story_nodes s
    WHERE s.status NOT IN ('concept', 'rejected', 'deprecated', 'infeasible', 'bugged')
      AND (SELECT COUNT(*) FROM story_paths WHERE ancestor_id = s.id AND depth = 1) <
          COALESCE(s.capacity, 3 + (SELECT COUNT(*) FROM story_paths sp
               JOIN story_nodes child ON sp.descendant_id = child.id
               WHERE sp.ancestor_id = s.id AND sp.depth = 1
               AND child.status IN ('implemented', 'ready')))
    ORDER BY node_depth ASC
    LIMIT 1
''')
result['capacity_nodes'] = [dict(row) for row in cursor.fetchall()]

# Find stories with 'refine' status (limit 2)
cursor.execute('''
    SELECT s.id, s.title, s.description, s.notes,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
    FROM story_nodes s
    WHERE s.status = 'refine'
    ORDER BY s.updated_at ASC
    LIMIT 2
''')
result['refine_nodes'] = [dict(row) for row in cursor.fetchall()]

print(json.dumps(result, indent=2))
conn.close()
"
```

### Step 2: Generate New Story for Under-Capacity Node

If `capacity_nodes` from Step 1 contains a node, invoke the `story-writing` skill:

1. Use the Skill tool to invoke `story-writing`
2. Pass the discovered node ID (e.g., "Generate 1 story for node 1.2")
3. Generate exactly 1 story

**Why limit to 1?** With refinements now prioritized, keeping new story generation minimal ensures quality focus. The skill gets called again if more capacity exists.

### Step 3: Refine Stories Needing Rework

For each story in `refine_nodes` from Step 1:

#### 3.1: Analyze the Refinement Feedback

1. Read the story's current `description` field (contains the existing user story)
2. Read the story's `notes` field (contains feedback explaining why it wasn't approved and what refinements were suggested)
3. Understand the history and specific changes requested

#### 3.2: Archive Previous Story Version to Notes

Append the current story description to the notes field with a timestamp, preserving the refinement history:

```python
python -c "
import sqlite3
from datetime import datetime

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Get current story data
cursor.execute('SELECT description, notes FROM story_nodes WHERE id = ?', ('STORY_ID',))
row = cursor.fetchone()
current_description = row[0]
current_notes = row[1] or ''

# Create archive entry with timestamp
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
archive_entry = f'''

---
**Previous Version ({timestamp}):**
{current_description}
---
'''

# Append to notes
updated_notes = current_notes + archive_entry

cursor.execute('UPDATE story_nodes SET notes = ? WHERE id = ?', (updated_notes, 'STORY_ID'))
conn.commit()
conn.close()
print('Previous story version archived to notes')
"
```

#### 3.3: Generate Refined User Story

Based on the feedback in notes, create a new refined user story that addresses the concerns:

1. Review the original story (now archived in notes)
2. Identify specific feedback points from the notes
3. Generate a new user story that:
   - Addresses each feedback point
   - Maintains the core intent of the original story
   - Follows the proper user story format (As a/I want/So that)
   - Has improved acceptance criteria based on feedback

**Story Format Template:**

```markdown
**As a** [specific user role]
**I want** [specific capability - refined based on feedback]
**So that** [specific benefit - clarified based on feedback]

**Acceptance Criteria:**
- [ ] [Specific, testable criterion - addressing feedback]
- [ ] [Specific, testable criterion - addressing feedback]
- [ ] [Specific, testable criterion - addressing feedback]

**Refinement Notes:** [Brief summary of what changed from previous version based on feedback]
```

#### 3.4: Update Story with Refined Version

Update the story's description with the new refined story and change status to 'concept':

```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

new_description = '''REFINED_STORY_DESCRIPTION'''

cursor.execute('''
    UPDATE story_nodes
    SET description = ?, status = 'concept', updated_at = datetime('now')
    WHERE id = ?
''', (new_description, 'STORY_ID'))

conn.commit()
conn.close()
print('Story refined and status updated to concept')
"
```

### Step 4: Report Results

Output a summary showing:

#### Stories Refined (Priority)
- Which stories had status 'refine' (up to 2)
- Summary of feedback addressed for each
- Confirmation that status changed to 'concept'

#### New Story Generated
- Which node was identified as having capacity (if any)
- The story that was generated
- Note if more capacity nodes exist for next run

## With Arguments

When arguments are provided, pass them directly to the story-writing skill as instructions.

**Maximum limit**: Even with arguments, never generate more than 10 stories total. If the user requests more than 10, cap at 10 and inform them of the limit.

**Examples:**
- `/write-story for node 1.2` → Generate stories specifically for node 1.2
- `/write-story focus on user authentication features` → Generate stories related to authentication
- `/write-story 3 stories for the export module` → Generate 3 stories for export functionality
- `/write-story 10 stories for node 1` → Generate 10 stories (maximum allowed)
- `/write-story refine 1.3.2` → Manually trigger refinement for a specific story

Use the Skill tool to invoke `story-writing` with the user's instructions.

## Status Flow

```
concept → approved → planned → active → implemented → released
    ↓         ↓
 refine  →  (this command refines and returns to concept)
    ↓
 rejected
```

When a story has status 'refine':
1. Notes contain feedback explaining why approval was not granted
2. This command archives the current story to notes
3. Creates a refined version addressing the feedback
4. Resets status to 'concept' for fresh review
