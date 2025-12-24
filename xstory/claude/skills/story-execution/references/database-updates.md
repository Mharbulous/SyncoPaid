# Database Updates

SQL patterns for updating story status during execution.

**Database:** `.claude/data/story-tree.db`
**Critical:** Use Python sqlite3 module, NOT sqlite3 CLI.

## CI Mode Usage

The `python -c "..."` examples below require approval in CI mode. Instead:
1. Write the script to `.claude/skills/story-execution/temp-db-update.py`
2. Run with `python .claude/skills/story-execution/temp-db-update.py`
3. Delete the script after (optional)

## Stage Transitions

### Execution Started (Step 2 → proceeding)

```python
python -c "
import sqlite3

story_id = '[STORY_ID]'
conn = sqlite3.connect('.claude/data/story-tree.db')

conn.execute('''
    UPDATE story_nodes
    SET stage = 'active',
        notes = COALESCE(notes || chr(10), '') || 'Execution started: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

conn.commit()
print(f'Story {story_id} stage updated to active')
conn.close()
"
```

### Execution Paused (CI Mode - blocking issues)

```python
python -c "
import sqlite3

story_id = '[STORY_ID]'
blocking_issues = 'Description of blocking issues'
conn = sqlite3.connect('.claude/data/story-tree.db')

# Stage stays 'active', hold_reason indicates why stopped
conn.execute('''
    UPDATE story_nodes
    SET hold_reason = 'paused', human_review = 1,
        notes = COALESCE(notes || chr(10), '') || 'PAUSED - Blocking issues require human decision: ' || datetime('now') || chr(10) || ?,
        updated_at = datetime('now')
    WHERE id = ?
''', (blocking_issues, story_id))

conn.commit()
print(f'Story {story_id} paused for human review')
conn.close()
"
```

### Execution Complete - Review Required

```python
python -c "
import sqlite3

story_id = '[STORY_ID]'
conn = sqlite3.connect('.claude/data/story-tree.db')

conn.execute('''
    UPDATE story_nodes
    SET stage = 'reviewing', human_review = 1,
        notes = COALESCE(notes || chr(10), '') || 'Awaiting human review of CI decisions: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

conn.commit()
print(f'Story {story_id} stage updated to reviewing')
conn.close()
"
```

### Execution Complete - Verification Required

```python
python -c "
import sqlite3

story_id = '[STORY_ID]'
conn = sqlite3.connect('.claude/data/story-tree.db')

conn.execute('''
    UPDATE story_nodes
    SET stage = 'verifying', human_review = 0,
        notes = COALESCE(notes || chr(10), '') || 'Execution complete, awaiting verification: ' || datetime('now'),
        updated_at = datetime('now')
    WHERE id = ?
''', (story_id,))

conn.commit()
print(f'Story {story_id} stage updated to verifying')
conn.close()
"
```

## Commit Linking

Link commits to story for traceability:

```python
python -c "
import sqlite3

story_id = '[STORY_ID]'
commit_hash = '[COMMIT_HASH]'
commit_message = '[COMMIT_MESSAGE]'

conn = sqlite3.connect('.claude/data/story-tree.db')

conn.execute('''
    INSERT OR IGNORE INTO story_commits (story_id, commit_hash, commit_date, commit_message)
    VALUES (?, ?, datetime('now'), ?)
''', (story_id, commit_hash, commit_message))

conn.commit()
print(f'Linked commit {commit_hash} to story {story_id}')
conn.close()
"
```

## Link All Batch Commits

After batch completion, link all commits from temp-CI-notes.json:

```python
python -c "
import json, sqlite3

story_id = '[STORY_ID]'
state_file = '.claude/skills/story-execution/temp-CI-notes.json'

with open(state_file) as f:
    state = json.load(f)

conn = sqlite3.connect('.claude/data/story-tree.db')

for batch in state.get('batches', []):
    for commit_hash in batch.get('commits', []):
        conn.execute('''
            INSERT OR IGNORE INTO story_commits (story_id, commit_hash, commit_date, commit_message)
            VALUES (?, ?, datetime('now'), ?)
        ''', (story_id, commit_hash, f'Batch {batch[\"batch\"]} commit'))

conn.commit()
print(f'Linked {sum(len(b.get(\"commits\", [])) for b in state.get(\"batches\", []))} commits to story {story_id}')
conn.close()
"
```
