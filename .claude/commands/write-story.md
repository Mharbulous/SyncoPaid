Generate new user story concepts using the brainstorm-story skill, or refine existing stories that need rework.

## Arguments

- **With arguments**: Pass the arguments as instructions to the brainstorm-story skill (e.g., `/write-story for node 1.2` or `/write-story focus on export features`)
- **Without arguments**: Auto-discover nodes with capacity for new stories AND nodes with status 'refine' that need rework

## Default Behavior (No Arguments)

When invoked without arguments, the command performs two distinct operations:
1. **Generate new stories** for nodes with capacity
2. **Refine existing stories** that have status 'refine'

### Step 1: Discover All Nodes Needing Attention

Query the story-tree database in a single call to find:
- Up to 2 nodes with capacity for new stories
- Up to 3 stories needing refinement (status 'refine')

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
    LIMIT 2
''')
result['capacity_nodes'] = [dict(row) for row in cursor.fetchall()]

# Find stories with 'refine' status (limit 3)
cursor.execute('''
    SELECT s.id, s.title, s.description, s.notes,
        (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth
    FROM story_nodes s
    WHERE s.status = 'refine'
    ORDER BY s.updated_at ASC
    LIMIT 3
''')
result['refine_nodes'] = [dict(row) for row in cursor.fetchall()]

print(json.dumps(result, indent=2))
conn.close()
"
```

### Step 2: Generate New Stories for Under-Capacity Nodes (Batched)

If `capacity_nodes` from Step 1 contains any nodes, invoke the `brainstorm-story` skill **once** with all target nodes:

1. Use the Skill tool to invoke `brainstorm-story`
2. Pass ALL discovered node IDs together (e.g., "Generate stories for nodes: 1.2, 1.3")
3. Request 1 story per node, max 2 stories total

**Why batch?** Invoking the skill once with multiple nodes avoids repeatedly loading skill instructions, saving ~1,400 tokens per additional node.

**Distribution strategy**: The skill will generate stories round-robin across provided nodes, prioritizing shallower nodes, until 2 stories total are created.

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

#### New Stories Generated
- Which nodes were identified as having capacity
- How many stories were generated for each
- Total new stories created

#### Stories Refined
- Which stories had status 'refine'
- Summary of feedback addressed for each
- Confirmation that status changed to 'concept'

## With Arguments

When arguments are provided, pass them directly to the brainstorm-story skill as instructions.

**Maximum limit**: Even with arguments, never generate more than 10 stories total. If the user requests more than 10, cap at 10 and inform them of the limit.

**Examples:**
- `/write-story for node 1.2` → Generate stories specifically for node 1.2
- `/write-story focus on user authentication features` → Generate stories related to authentication
- `/write-story 3 stories for the export module` → Generate 3 stories for export functionality
- `/write-story 10 stories for node 1` → Generate 10 stories (maximum allowed)
- `/write-story refine 1.3.2` → Manually trigger refinement for a specific story

Use the Skill tool to invoke `brainstorm-story` with the user's instructions.

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
