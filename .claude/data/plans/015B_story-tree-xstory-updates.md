# Sub-Plan B: xstory.py Updates for Three-Field Display

## Overview

Update the xstory.py TUI to read and display the new `story` and `success_criteria` fields in the DetailView.

**Parent Plan**: 015_story-tree-three-field-migration.md
**Depends On**: 015A (schema columns must exist)

---

## TDD Tasks

### Task 1: Update StoryNode dataclass with new fields

**File**: `dev-tools/xstory/xstory.py`

Update the StoryNode class to include:
```python
story: str = ''
success_criteria: str = ''
```

**Location**: Around line 428 in StoryNode `__init__`

**Verify**: `python -c "from xstory import StoryNode; s = StoryNode('1','t','s',1, story='test'); print(s.story)"`

---

### Task 2: Update SQL query in _load_nodes()

**File**: `dev-tools/xstory/xstory.py`

Update the SELECT query to include:
```sql
s.story, s.success_criteria
```

And update the row unpacking to map these fields to StoryNode.

**Location**: Around line 1527

**Verify**: Load xstory and verify no SQL errors when opening the application

---

### Task 3: Update DetailView._update_detail() for three-field display

**File**: `dev-tools/xstory/xstory.py`

Replace the current description display with three sections:
1. **Story** - User story format (if present)
2. **Success Criteria** - Acceptance checklist (if present)
3. **Description** - Additional context (if present)

Use `_add_section_header()` for each section.

**Location**: Around line 825

**Verify**:
```bash
cd dev-tools/xstory
python xstory.py
# Select a node and verify the DetailView shows separate sections
```

---

### Task 4: Fallback display for unmigrated nodes

Ensure DetailView gracefully handles nodes where:
- `story` is empty but `description` has content (pre-migration)
- All new fields are empty
- Only some fields have content

**Verify**: Create a test node with only description content, verify it displays correctly

---

## Verification Checklist

- [ ] StoryNode class has story and success_criteria attributes
- [ ] SQL query includes new columns without errors
- [ ] DetailView shows three sections for migrated nodes
- [ ] DetailView handles pre-migration nodes gracefully
- [ ] xstory.py starts without errors
