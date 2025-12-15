Generate new user story concepts using the brainstorm-story skill.

## Arguments

- **With arguments**: Pass the arguments as instructions to the brainstorm-story skill (e.g., `/write-stories for node 1.2` or `/write-stories focus on export features`)
- **Without arguments**: Auto-discover nodes with capacity and generate stories

## Default Behavior (No Arguments)

When invoked without arguments, automatically find nodes that have capacity for new concepts and generate up to 2 total user stories.

### Step 1: Find Nodes with Capacity

Query the story-tree database to find up to 2 nodes that can accept new concept stories:

```python
python -c "
import sqlite3
import json

conn = sqlite3.connect('.claude/data/story-tree.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find under-capacity nodes, shallower first
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

nodes = [dict(row) for row in cursor.fetchall()]
print(json.dumps(nodes, indent=2))
conn.close()
"
```

### Step 2: Generate Stories

For each node found (up to 2 total stories across all nodes):

1. Use the Skill tool to invoke `brainstorm-story`
2. Pass the node ID and request stories be generated
3. Track story count to stop at 2 total

**Distribution strategy**: Generate stories round-robin across discovered nodes until 2 stories are created, prioritizing shallower nodes.

### Step 3: Report Results

Output a summary showing:
- Which nodes were identified as having capacity
- How many stories were generated for each
- Total stories created

## With Arguments

When arguments are provided, pass them directly to the brainstorm-story skill as instructions.

**Maximum limit**: Even with arguments, never generate more than 10 stories total. If the user requests more than 10, cap at 10 and inform them of the limit.

**Examples:**
- `/write-stories for node 1.2` → Generate stories specifically for node 1.2
- `/write-stories focus on user authentication features` → Generate stories related to authentication
- `/write-stories 3 stories for the export module` → Generate 3 stories for export functionality
- `/write-stories 10 stories for node 1` → Generate 10 stories (maximum allowed)

Use the Skill tool to invoke `brainstorm-story` with the user's instructions.
