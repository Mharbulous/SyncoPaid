# Sub-Plan B: xstory.py UI Updates

## Overview

Update xstory.py to read from and display the new `story` and `success_criteria` fields in the DetailView.

Parent plan: `015_story-tree-three-field-migration.md`
Depends on: `015A_story-tree-migration-script.md` (columns must exist in database)

---

## TDD Tasks

### Task 1: Update StoryNode class

**File**: `dev-tools/xstory/xstory.py`

**Test**:
```python
# StoryNode should accept and store new fields
node = StoryNode(
    id="test", title="Test", status="open", capacity=1,
    story="As a user...", success_criteria="- [ ] Done"
)
assert node.story == "As a user..."
assert node.success_criteria == "- [ ] Done"
```

**Implementation**:
- Add `story: str = ''` parameter to `__init__`
- Add `success_criteria: str = ''` parameter to `__init__`
- Store as instance attributes

---

### Task 2: Update SQL query in _load_nodes()

**Test**:
```sql
-- Query should return new columns
SELECT s.story, s.success_criteria FROM story_nodes s LIMIT 1;
```

**Implementation**:
- Add `s.story, s.success_criteria` to SELECT clause
- Update row unpacking to include new fields
- Pass new fields to StoryNode constructor

---

### Task 3: Update DetailView._update_detail() display

**Test (manual)**:
- Open xstory GUI
- Select a story with migrated content
- Verify three separate sections: Story, Success Criteria, Description

**Implementation**:
- Add "Story" section header when `node.story` is non-empty
- Add "Success Criteria" section header when `node.success_criteria` is non-empty
- Keep "Description" section for remaining content
- Preserve existing Notes section unchanged

---

## Completion Criteria

- [ ] StoryNode class accepts new fields
- [ ] SQL query fetches new columns
- [ ] DetailView displays Story section
- [ ] DetailView displays Success Criteria section
- [ ] DetailView displays Description section (remaining content)
- [ ] Notes section unchanged
