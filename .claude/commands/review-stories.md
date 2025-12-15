Review user story concepts one at a time for approval.

## Purpose

Present the most suitable concept story for user review, allowing them to approve, reject, refine, or wishlist it.

## Workflow

### Step 1: Find Concept Stories

Query the story-tree database for all stories with status 'concept', prioritizing by depth (shallower first) and creation date (oldest first):

```python
python -c "
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT s.id, s.title, s.description, s.created_at,
           (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id) as node_depth,
           (SELECT title FROM story_nodes p
            JOIN story_paths sp ON p.id = sp.ancestor_id
            WHERE sp.descendant_id = s.id AND sp.depth = 1) as parent_title
    FROM story_nodes s
    WHERE s.status = 'concept'
    ORDER BY node_depth ASC, s.created_at ASC
    LIMIT 1
''')

row = cursor.fetchone()
conn.close()

if row:
    id, title, desc, created, depth, parent = row
    print(f'ID: {id}')
    print(f'Title: {title}')
    print(f'Parent: {parent or \"root\"}')
    print(f'Depth: {depth}')
    print(f'Created: {created}')
    print(f'---DESCRIPTION---')
    print(desc)
else:
    print('NO_CONCEPTS_FOUND')
"
```

### Step 2: Present Story for Review

If a concept story is found, present it in this format:

```markdown
## Story for Review: **[Title]**

| Field | Value |
|-------|-------|
| **ID** | [id] |
| **Parent** | [parent_title] |
| **Status** | concept |
| **Created** | [created_at] |

### User Story

[Full description from database]

---

**Your options:**
- **Approve** → Story is ready for planning/implementation
- **Reject** → Story is not wanted (provide reason)
- **Refine** → Story needs more detail or clarification
- **Wishlist** → Nice to have, low priority
```

### Step 3: Handle User Response

Wait for user input. Based on their response:

**If user wants to approve:**
- Ask if they have any refinements to make first
- If yes, make the edits then mark as approved
- If no, mark as approved directly

**If user wants to reject:**
- Ask for reason (optional)
- Mark as rejected

**If user wants to refine:**
- Mark as refine (needs more detail)

**If user wants to wishlist:**
- Mark as wishlist (low priority)

**Update query:**
```python
python -c "
import sqlite3
conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()
cursor.execute('''
    UPDATE story_nodes
    SET status = '[NEW_STATUS]', updated_at = datetime('now')
    WHERE id = '[STORY_ID]'
''')
conn.commit()
conn.close()
print('Story [STORY_ID] marked as [NEW_STATUS]')
"
```

### Step 4: Commit Changes

After updating the story status, commit and push:
- `git add .claude/data/story-tree.db`
- Commit with message: `feat(stories): [action] story [id] - [title]`
- Push to current branch

### If No Concepts Found

If no concept stories exist, inform the user:

```
No concept stories awaiting review.

To generate new stories, use `/write-stories` or invoke the `brainstorm-story` skill.
```

## Notes

- Review only ONE story per invocation to keep reviews focused
- Always present the full story description so user has complete context
- Encourage user to suggest refinements before approving
